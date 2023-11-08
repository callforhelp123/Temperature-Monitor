import requests

# Define the API URL
owm_api_key = "5f1d3a5a193fe9ed245cd087ddc305a9"

weather = requests.get(
    f"https://api.openweathermap.org/data/2.5/onecall?lat={47.6}&lon={-122.3}&exclude=minutely&appid={owm_api_key}&units=imperial")
weather = weather.json()
temp = weather["current"]["temp"]
print(temp)




from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart 
from password import returnPassword
import smtplib 

# initialize connection to our email server, we will use gmail here 
smtp = smtplib.SMTP('smtp.gmail.com', 587) 
smtp.ehlo() 
smtp.starttls() 
password = returnPassword()
# Login with your email and password 
print(password)
smtp.login('tempsensor486@gmail.com', password) 
  
  
# send our email message 'msg' to our boss  
msg = MIMEMultipart() 
msg['Subject'] = "test subject"  
msg.attach(MIMEText("test body"))   

  
# Make a list of emails, where you wanna send mail 
to = ["snowsoftj4c@gmail.com"] 
  
# Provide some data to the sendmail function! 
smtp.sendmail(from_addr="hello@gmail.com", 
              to_addrs=to, msg=msg.as_string()) 
  
 # Finally, don't forget to close the connection 
smtp.quit()
