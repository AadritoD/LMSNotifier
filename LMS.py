import requests
from bs4 import BeautifulSoup
from io import BytesIO
from pdfminer.high_level import extract_text
import subprocess
import anthropic
import time
import warnings
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class LMS:
    
    def login(self):
        login_page = self.session.get('https://lms.vit.ac.in/login/index.php', verify=False)
        page = BeautifulSoup(login_page.text, 'html.parser')
        token = page.find('input', {'name': 'logintoken'}).attrs['value']
        data = {'anchor': '', 'logintoken': token, 'username': '22bai1407', 'password': 'REDACTED', 'rememberusername': 1}
        print(data)
        self.session.post("https://lms.vit.ac.in/login/index.php", data, verify=False)
    
    def __init__(self):
        self.session = requests.Session()
        self.login()
        self.font_name = "Arial"
        self.font_size = 12
        
    def reload(self):
        self.session = requests.Session()
        self.login()
        
    def pending_questions(self, id: int) -> list[str]:
        page = BeautifulSoup(self.session.get(f"https://lms.vit.ac.in/course/view.php?id={id}", verify=False).text, 'html.parser')
        task_list = page.find('button', {'class': 'btn btn-outline-success'}).parent.parent.parent.parent.parent.parent.parent
        retval = [task.a.attrs['href'] for task in task_list if "Done" not in task.get_text() and "Restricted" not in task.get_text()]
        return retval
    
    def read_pdf(self, pdf_url: str):
        response = self.session.get(pdf_url, verify=False)
        if response.status_code == 200:
            with BytesIO(response.content) as pdf_file:
                text = extract_text(pdf_file)
                return text
        else:
            raise Exception(f"Failed to download PDF: {response.status_code}")
        
    def get_pdf(self, link: str):
        page = BeautifulSoup(self.session.get(link, verify=False).text, 'html.parser')
        file_link = page.find('a', {'target': '_blank'})
        if file_link:
            return self.read_pdf(file_link.attrs['href'])

def answer(question: str, token_limit=4000) -> str:
    client = anthropic.Anthropic(
        api_key="REDACTED",
    )
    
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=token_limit,
        temperature=0,
        system="Solve all of the following questions",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    }   
                ]
            }
        ]
    )
    return message.content[0].text

def send_email(subject: str, body: str, to_email: str):
    from_email = "aadrito.datta@gmail.com"
    from_password = "REDACTED"
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    server = smtplib.SMTP('smtp.example.com', 587)
    server.starttls()
    server.login(from_email, from_password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

done_list = set()
lms = LMS()

def main_loop(subjects):
    global done_list
    global lms
    for subject in subjects:
        for val in lms.pending_questions(subject):
            if val and val not in done_list:
                done_list.add(val)
                pdf = lms.get_pdf(val)
                solution = answer(pdf)
                send_email("New Homework Found", f"New homework found for subject {subject}. Draft solution:\n\n{solution}", "aadrito.datta@gmail.com")
                print(f'sai_what{len(done_list)}')

def main(subjects):
    while True:
        print(f"BEGIN MAIN LOOP: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
        main_loop(subjects)
        time.sleep(30)

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    subjects = [4229, 4698]
    while True:
        try:
            main(subjects)
        except Exception as e:
            lms.reload()
            print(e)
