import streamlit as st
import re
import sqlite3
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from datetime import datetime

# Set your API keys
YOUTUBE_API_KEY = "your_youtube_api_key"
OPENAI_API_KEY = "your_openai_api_key"

# Initialize the API clients
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)

# Initialize SQLite database
conn = sqlite3.connect('blogstream.db')
c = conn.cursor()

# Check if the read and created_at columns exist, and add them if they don't
try:
    c.execute('SELECT read FROM blogs LIMIT 1')
except sqlite3.OperationalError:
    c.execute('ALTER TABLE blogs ADD COLUMN read INTEGER DEFAULT 0')
    conn.commit()

try:
    c.execute('SELECT created_at FROM blogs LIMIT 1')
except sqlite3.OperationalError:
    c.execute('ALTER TABLE blogs ADD COLUMN created_at TEXT')
    conn.commit()

c.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS blog_tags (
        blog_id INTEGER,
        tag_id INTEGER,
        FOREIGN KEY (blog_id) REFERENCES blogs (id),
        FOREIGN KEY (tag_id) REFERENCES tags (id)
    )
''')
conn.commit()

def get_video_id(url):
    short_url_match = re.match(r'https://youtu.be/([^?&]+)', url)
    long_url_match = re.match(r'.*v=([^&]+).*', url)

    if short_url_match:
        return short_url_match.group(1)
    elif long_url_match:
        return long_url_match.group(1)
    else:
        raise ValueError('Invalid YouTube URL')

def fetch_transcript(video_id):
    return YouTubeTranscriptApi.get_transcript(video_id)

def transcript_to_text(transcript, limit_tokens=1000):
    text = "\n".join([entry['text'] for entry in transcript])
    return text[:limit_tokens]  # Limit the transcript text to control tokens

def fetch_comments(video_id, max_comments=5):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_comments,
        textFormat="plainText"
    )
    response = request.execute()

    for item in response.get('items', []):
        comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
        comments.append(comment)

    return comments

def get_video_details(video_id):
    request = youtube.videos().list(part="snippet", id=video_id)
    response = request.execute()
    if 'items' in response and len(response['items']) > 0:
        video = response['items'][0]
        return {
            'title': video['snippet']['title'],
            'description': video['snippet']['description']
        }
    else:
        return {'title': "Untitled", 'description': ""}

def generate_blog(transcript_text, video_title, video_description, comments):
    comments_text = "\n".join(comments)
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": """
        Transform the following YouTube transcript into an engaging educational blog article. Structure your article as follows:
        1. Title: Create an attention-grabbing title that reflects the main topic of the video.
        2. Introduction: Write a brief, engaging introduction that outlines the video's main topic and why it's important or interesting.
        3. Main Body:
           - Divide the content into 3-5 main sections, each focusing on a key concept or idea from the video
           - Use subheadings for each section
           - Explain each concept in detail, using examples or analogies from the video
           - Include relevant quotes from the transcript to support your points
           - Incorporate any important data, research findings, or statistics mentioned
        4. Practical Application (if applicable):
           - If the video includes a tutorial or practical demonstration, include a "How-To" section
           - Break down the process into clear, numbered steps
           - Add any tips, warnings, or best practices mentioned in the video
        5. Conclusion:
           - Summarize the key takeaways from the video
           - Encourage readers to apply what they've learned or explore the topic further
        Use a conversational yet informative tone throughout the article. Include relevant keywords for SEO purposes. Format the article using markdown for better readability.
        Video Title: [Insert video title here]
        Video Description: [Insert video description here]
        Transcript:
        [Insert YouTube transcript here]
            """},
            {"role": "user", "content": f"Video Title: {video_title}\nVideo Description: {video_description}\nTranscript: {transcript_text}\nComments: {comments_text}"}
        ]
    )
    return response.choices[0].message.content

def generate_tags(blog_content):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a tagging assistant. Extract relevant tags from the blog content."},
            {"role": "user", "content": f"Blog Content: {blog_content}\n\nExtract relevant tags separated by commas."}
        ]
    )
    tags_text = response.choices[0].message.content
    return [tag.strip() for tag in tags_text.split(',')]

def save_blog_to_db(title, blog_content, tags):
    created_at = datetime.now().isoformat()
    c.execute('''
        INSERT INTO blogs (title, content, created_at)
        VALUES (?, ?, ?)
    ''', (title, blog_content, created_at))
    blog_id = c.lastrowid

    for tag in tags:
        c.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag,))
        c.execute('SELECT id FROM tags WHERE name = ?', (tag,))
        tag_id = c.fetchone()[0]
        c.execute('INSERT INTO blog_tags (blog_id, tag_id) VALUES (?, ?)', (blog_id, tag_id))

    conn.commit()

def get_all_blogs():
    c.execute('SELECT id, title, created_at FROM blogs ORDER BY id DESC')
    return c.fetchall()

def delete_blog(blog_id):
    c.execute('DELETE FROM blogs WHERE id = ?', (blog_id,))
    c.execute('DELETE FROM blog_tags WHERE blog_id = ?', (blog_id,))
    conn.commit()

def mark_blog_as_read(blog_id):
    c.execute('UPDATE blogs SET read = 1 WHERE id = ?', (blog_id,))
    conn.commit()

def search_blogs_by_tags(tags):
    tag_ids = []
    for tag in tags:
        c.execute('SELECT id FROM tags WHERE name = ?', (tag,))
        tag_id = c.fetchone()
        if tag_id:
            tag_ids.append(tag_id[0])

    if not tag_ids:
        return []

    query = '''
        SELECT DISTINCT b.id, b.title, b.created_at
        FROM blogs b
        JOIN blog_tags bt ON b.id = bt.blog_id
        WHERE bt.tag_id IN ({seq})
        ORDER BY b.id DESC
    '''.format(seq=','.join(['?'] * len(tag_ids)))

    c.execute(query, tag_ids)
    return c.fetchall()

def get_tag_name(tag_id):
    c.execute('SELECT name FROM tags WHERE id = ?', (tag_id,))
    return c.fetchone()[0]

def format_datetime(datetime_str):
    dt = datetime.fromisoformat(datetime_str)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Initialize session state for read blogs
if 'read_blogs' not in st.session_state:
    st.session_state.read_blogs = set()

st.title("BlogStream 📖")

st.sidebar.title("Menu 📋")
page = st.sidebar.radio("Select a page:", ["Home 🏠", "My Blogs 📚", "Create Blog ✍️", "Search Blogs 🔍", "Profile 👤"])

if page == "Home 🏠":
    if 'selected_blog_id' in st.session_state:
        blog_id = st.session_state.selected_blog_id
        c.execute('SELECT title, content FROM blogs WHERE id = ?', (blog_id,))
        blog = c.fetchone()
        if blog:
            st.header(blog[0] + " 📝")
            st.write(blog[1])
            st.write("---")
            if st.button("Back to Newsfeed 🔙"):
                del st.session_state.selected_blog_id
                st.rerun()
    else:
        st.header("Newsfeed 📰")
        blogs = get_all_blogs()
        if blogs:
            for blog in blogs:
                title = blog[1] if blog[1] else "Untitled"
                button_text = f"📄 {title}"
                if st.button(button_text, key=blog[0]):
                    st.session_state.selected_blog_id = blog[0]
                    mark_blog_as_read(blog[0])
                    st.session_state.read_blogs.add(blog[0])
                    st.rerun()
        else:
            st.write("No blogs found. Create your first blog!")

elif page == "My Blogs 📚":
    st.header("My Blogs 📚")
    blogs = get_all_blogs()
    if blogs:
        for blog in blogs:
            title = blog[1] if blog[1] else "Untitled"
            created_at = format_datetime(blog[2]) if blog[2] else "Unknown date"
            st.subheader(f"📄 {title}")
            st.write(f"Created at: {created_at}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Read", key=f"read_{blog[0]}"):
                    st.session_state.selected_blog_id = blog[0]
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{blog[0]}"):
                    delete_blog(blog[0])
                    st.rerun()
            st.write("---")
    else:
        st.write("No blogs found. Create your first blog!")

elif page == "Create Blog ✍️":
    st.header("Create a New Blog ✍️")
    youtube_url = st.text_input("Enter YouTube URL")

    if st.button("Generate Blog 🚀"):
        try:
            video_id = get_video_id(youtube_url)
            video_details = get_video_details(video_id)
            title = video_details['title']
            description = video_details['description']
            transcript = fetch_transcript(video_id)
            transcript_text = transcript_to_text(transcript)
            comments = fetch_comments(video_id)

            with st.spinner("Generating blog... ⏳"):
                blog_content = generate_blog(transcript_text, title, description, comments)
                tags = generate_tags(blog_content)
                save_blog_to_db(title, blog_content, tags)
                st.success("Blog generated and saved successfully! 🎉")
                st.write(blog_content)

        except Exception as e:
            st.error(f"Error: {e} ❌")

elif page == "Search Blogs 🔍":
    st.header("Search Blogs by Tags 🔍")
    tag_input = st.text_input("Enter tags separated by commas")

    if st.button("Search 🔍"):
        tags = [tag.strip() for tag in tag_input.split(',')]
        blogs = search_blogs_by_tags(tags)
        if blogs:
            for blog in blogs:
                title = blog[1] if blog[1] else "Untitled"
                created_at = format_datetime(blog[2]) if blog[2] else "Unknown date"
                button_text = f"📄 {title} (Created at: {created_at})"
                if st.button(button_text, key=f"search_{blog[0]}"):
                    st.session_state.selected_blog_id = blog[0]
                    st.session_state.page = "Home 🏠"
                    st.experimental_rerun()
        else:
            st.write("No blogs found with the specified tags. ❌")

if 'selected_tag_id' in st.session_state:
    tag_id = st.session_state.selected_tag_id
    tag_name = get_tag_name(tag_id)
    blogs = search_blogs_by_tags([tag_name])
    if blogs:
        st.header(f"Blogs with tag: {tag_name}")
        for blog in blogs:
            st.subheader(blog[1])
            st.write("---")
        if st.button("Back to Tags 🔙"):
            del st.session_state.selected_tag_id
            st.rerun()

# Correct the logic here to ensure the page switch works
if 'page' in st.session_state and st.session_state.page == "Home 🏠":
    st.session_state.page = None
    st.rerun()
