# BlogStream 📖

BlogStream is a powerful Streamlit-based web application that transforms YouTube videos into engaging blog posts using AI technology. By combining OpenAI's GPT models with YouTube's API, it automates the content creation process while maintaining high-quality, structured output.

## 🌟 Features

- **YouTube Integration**
  - Automatic video transcript extraction
  - Metadata retrieval (title, description, statistics)
  - Support for any public YouTube video

- **AI-Powered Content Generation**
  - Blog post creation using GPT-4
  - Intelligent tag generation with GPT-3.5
  - Natural language processing for coherent content

- **Content Management**
  - Create, read, and delete blog posts
  - Tag-based organization system
  - Advanced search functionality
  - User profile management

- **Data Persistence**
  - SQLite database integration
  - Efficient metadata storage
  - Robust tag management

## 🛠️ Tech Stack

- **Frontend Framework**
  - `streamlit`: Interactive web interface
  - Responsive design
  - User-friendly controls

- **AI Services**
  - `openai`: GPT model integration
  - Advanced language processing

- **YouTube Integration**
  - `youtube-transcript-api`: Transcript extraction
  - `google-api-python-client`: YouTube Data API v3

- **Database**
  - SQLite: Local data storage
  - Efficient query handling

## 📋 Prerequisites

- Python 3.8 or higher
- Poetry package manager
- YouTube API key
- OpenAI API key

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/kreativwiz1/blogstream
cd blogstream
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Configure API keys:
   - Open `main.py`
   - Add your API keys:
     ```python
     YOUTUBE_API_KEY = "your_youtube_api_key"
     OPENAI_API_KEY = "your_openai_api_key"
     ```

4. Launch the application:
```bash
streamlit run main.py
```

## 🗺️ Navigation

The application features an intuitive navigation structure:

| Section | Icon | Description |
|---------|------|-------------|
| Home | 🏠 | Dashboard with recent blog posts |
| My Blogs | 📚 | Personal blog management interface |
| Create Blog | ✍️ | New blog generation from YouTube videos |
| Search Blogs | 🔍 | Tag-based blog search system |
| Profile | 👤 | User profile and settings |

## 🚢 Deployment

BlogStream is configured for deployment on Cloud Run:

1. Review settings in `.replit`
2. Ensure environment variables are properly set
3. Follow Cloud Run deployment guidelines

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📮 Contact

For support or queries, please open an issue in the GitHub repository.

## 🙏 Acknowledgments

- OpenAI for their GPT models
- YouTube API for video data access
- Streamlit team for their amazing framework
