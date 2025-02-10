from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send_emails", methods=["POST"])
def send_emails():
    try:
        sender_email = request.form["email_sender"]
        sender_password = request.form["email_password"]
        subject_template = request.form["subject"]
        message_body_template = request.form["message_body"]
        file = request.files["file"]
        image = request.files.get("image")

        # Save uploaded image (if provided)
        image_path = None
        if image:
            image_path = os.path.join(UPLOAD_FOLDER, image.filename)
            image.save(image_path)

        # Read Excel file
        df = pd.read_excel(file)

        if "Email" not in df.columns:
            return jsonify({"error": "Column 'Email' not found in Excel file."})

        success_count = 0
        failed_emails = []

        # Send email to each recipient
        for index, row in df.iterrows():
            recipient_email = row["Email"]

            # Replace placeholders with actual column values
            subject = subject_template
            message_body = message_body_template

            for col in df.columns:
                placeholder = f"{{{{{col}}}}}"
                if placeholder in subject:
                    subject = subject.replace(placeholder, str(row[col]))
                if placeholder in message_body:
                    message_body = message_body.replace(placeholder, str(row[col]))

            # Create Email
            msg = MIMEMultipart()
            msg["From"] = f"Ideal Media Marketing <{sender_email}>"
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg["X-Priority"] = "1"

            msg.attach(MIMEText(message_body, "html"))

            # Attach Image (if available)
            if image_path:
                with open(image_path, "rb") as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header("Content-Disposition", "attachment", filename=image.filename)
                    msg.attach(img)

            # SMTP Setup (For Hostinger)
            try:
                server = smtplib.SMTP("smtp.hostinger.com", 587)
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
                server.quit()
                success_count += 1
            except Exception as e:
                failed_emails.append(recipient_email)

        return jsonify({
            "success": f"Emails sent successfully: {success_count}",
            "failed": failed_emails
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
