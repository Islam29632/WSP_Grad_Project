# WSP Grad Project

# Team Members:

- [x] 1. [Islam Ali]
- [x] 2. [Peter Magdy Gamil]
- [x] 3. [Mostafa Saad]
- [x] 4. [Esraa Kamel]
- [x] 5. [Mohamed Khaled]
- [ ] [no contribute] 6. [Mahmoud Mohamed Elebiare]
- [ ] [no contribute] 7. [Mohamed Alaa Eldin Fouad Ahmed Mansour]

# Streamlit flowchart

```mermaid
graph TD
    A[Start] --> B{User Interface};
    B --> C[Login Page];
    C --> D{Authentication};
    D -- Success --> E[Main Dashboard];
    D -- Failure --> C;
    C --> F[Sign Up Page];
    F --> C;

    G[Start Application] --> H[Start API Server];
    H --> I[Start Streamlit App];
    I --> E;
```

# Agents flowchart

```mermaid
graph TD
    A[Start] --> B[Automated Dataset Pipeline];
    B --> C[Data Processing & Analysis];
    C --> D[Time Series Forecasting];
    D --> E[Recommendation Generation];
    E --> E1[Utilize RAG for Context];
    E --> E2[Fetch Real-time Data yfinance];
    E1 --> E;
    E2 --> E;
    E --> F[End];
```

# Demonastration video

## User Interface

### Login Page
<img src="resources/Login_page.jpg" title="Title" alt="title" width="35%">
The login page provides a secure entry point to the application. Users can enter their credentials which are verified against the hashed passwords in the database.

### Sign Up Page
<img src="resources/Sign_Up_page.jpg" title="Title" alt="title" width="35%">
New users can create an account through the sign-up page. The system validates the input and securely stores the credentials.

### Main Dashboard
<img src="resources/Main_page.jpg" title="Title" alt="title" width="35%">
After successful authentication, users are presented with the main dashboard where they can access the application's features.

# Setup the Application

```bash
pip install -r requirements.txt
```

# Running the Application

1. Start the API server first from the `project root directory`
```bash
uvicorn main:app
```
The API server will start on http://localhost:8000

2. Start the Streamlit app from the `frontend directory`
```bash
streamlit run app.py
```
The Streamlit app will be available at http://localhost:8501

Note: Make sure to start the API server before running the Streamlit app, as the frontend depends on the API being available.

# Technical Documentations

For detailed technical documentation about the authentication system, database structure, API endpoints, and security features, please refer to:
- [Database & Authentication Documentation](/docs/Authentication%20System%20Architecture.md)
