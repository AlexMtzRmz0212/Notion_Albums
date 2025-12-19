# Project Structure

```text
Notion_Albums/
├── src/
│   ├── __init__.py
│   ├── app.py              # Main Streamlit app
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base.py         # Base classes
│   │   ├── models.py       # Dataclasses
│   │   └── utils.py        # Shared utilities
│   └── managers/
│       ├── __init__.py
│       ├── sorter.py       # AlbumSorter functionality
│       └── decorator.py    # Cover functionality
├── .env
├── requirements.txt
└── README.md
```
---
## 🚀 Next Implementations

### Planned Features

Here are the upcoming features and improvements planned for Notion_Albums:

#### **Implementations**

- **Cancel Buttons When Running**  
  Add ability to cancel ongoing operations (like album sorting or cover updates) mid-execution for better user control in the Streamlit interface.

- **Song Management**  
  Extend functionality to include song-level operations, allowing users to organize and manage individual tracks within albums directly from the web interface.

- **Cover Update Error Reporting**  
  Implement detailed error explanations when album covers fail to update, providing users with specific reasons (e.g., "Image not found," "API rate limit exceeded," "Invalid image URL") to help troubleshoot issues.

- **Automatic Information Search and Update**  
  Create functionality to automatically fetch and populate missing database information, ensuring the library stays up-to-date with minimal manual entry.

#### **Improvements**

- **Search Specific Cover**  
  Implement targeted cover search functionality within the Streamlit app to find and apply specific album artwork.

- **Playoffs Ranking System**  
  Develop a competitive "playoff-style" ranking system to evaluate and sort songs or albums against each other for more dynamic user preferences.
---

### Feature Requests

Have ideas for more features? Feel free to:
- Open an [Issue](../../issues/new) with the "enhancement" label
- Suggest improvements to any part of the application
- Propose new features for the backend, frontend, or overall architecture

---

# Join the Development

I'd love to collaborate with others on this project! Whether you're interested in:

- **Backend development** – Improving the core Notion API integration, data models, or album management logic  
- **Frontend development** – Enhancing the Streamlit interface with better UI/UX  
- **New features** – Building out the planned implementations or adding your own ideas  
- **Bug fixes** – Helping improve the reliability and error handling  

This is a great opportunity to:

- Work with Notion's API and Python  
- Contribute to a practical, music-focused productivity tool  
- Learn about or share knowledge on Streamlit app development  

If any of these planned features interest you, or if you have your own ideas for the project, please reach out! I'm open to discussing how we can work together to make **Notion_Albums** even better.

You can start by:

1. Checking out the codebase – the structure is designed to be modular and approachable  
2. Trying out the current version to understand how it works  
3. Opening an issue to discuss your ideas or questions  

### About Me
If you'd like to see my other work or connect:
- [My GitHub Profile](https://github.com/AlexMtzRmz0212)
- [My Portfolio](https://alexmtzrmz0212.github.io/MyPortfolio/)
- [Email me](mailto:alejandro.martinez.rmz97@gmail.com)

---
*I'm always happy to discuss this project with fellow developers and music enthusiasts. Your input could help shape where this goes next! 🎵*

---
