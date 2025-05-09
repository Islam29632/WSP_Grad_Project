# WSP Grad Project

# Team Members:

- [x] 1. [Islam Ali]
- [x] 2. [Peter Magdy Gamil]
- [ ] [no contribute yet] 3. [Mostafa Saad]
- [ ] [no contribute yet] 4. [Mohamed Khaled]
- [ ] [no contribute yet] 5. [Esraa Kamel]
- [ ] [no contribute yet] 6. [Mahmoud Mohamed Elebiare]
- [ ] [no contribute yet] 7. [Mohamed Alaa Eldin Fouad Ahmed Mansour]

# How to contribute
1. Fork the repository 
```bash
git clone https://github.com/Islam29632/WSP_Grad_Project.git
```
2. install dependencies
```bash
pip install -r requirements.txt
```
3. Make your changes
4. Commit your changes
```bash
git add .
git commit -m "your message"
```
5. Push 
```bash
git push
```

# Running the Application

1. Start the API server first:
# From the project root directory
```bash
uvicorn main:app
```
The API server will start on http://localhost:8000

2. Start the Streamlit app:
```bash
# From the frontend directory
streamlit run app.py
```
The Streamlit app will be available at http://localhost:8501

Note: Make sure to start the API server before running the Streamlit app, as the frontend depends on the API being available.

# Check `TODO.md` file for tasks.