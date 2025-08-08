from flask import Flask, render_template, request, send_file
import pandas as pd
import joblib
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import sqlite3

# Initialize the Flask app
app = Flask(__name__)

# Load the trained model
model = joblib.load("performance_model.pkl")

# Define the features expected in the input
FEATURES = ["Hours Studied", "Previous Scores_scaled", "Extracurricular Activities",
            "Sleep Hours", "Sample Question Papers Practiced"]

# Create a directory to store PDF reports if it doesn't exist
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# Setup SQLite database
DB_FILE = "performance_data.db"
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                hours_studied REAL,
                previous_scores_scaled REAL,
                extracurricular_activities INTEGER,
                sleep_hours REAL,
                sample_question_papers_practiced INTEGER,
                predicted_class INTEGER,
                timestamp TEXT
            )
        """)
        conn.commit()

init_db()

@app.route("/")
def home():
    return render_template('index5.html')

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = {}
        if request.form:
            data = request.form.to_dict()
            try:
                student_name = data.get("Name", "Student")
                data_numeric = {key: float(value) for key, value in data.items() if key in FEATURES}
            except ValueError:
                return "Invalid input, unable to convert to float", 400

            if not all(feature in data_numeric for feature in FEATURES):
                return f"Missing one or more required features: {FEATURES}", 400

            input_data = pd.DataFrame([data_numeric])
            prediction = model.predict(input_data)
            predicted_class = int(prediction[0])

            # Store in DB
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO predictions (
                        name, hours_studied, previous_scores_scaled,
                        extracurricular_activities, sleep_hours,
                        sample_question_papers_practiced, predicted_class, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_name,
                    data_numeric["Hours Studied"],
                    data_numeric["Previous Scores_scaled"],
                    int(data_numeric["Extracurricular Activities"]),
                    data_numeric["Sleep Hours"],
                    int(data_numeric["Sample Question Papers Practiced"]),
                    predicted_class,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()

            guidance = generate_guidance(predicted_class)
            pdf_filename = generate_pdf(student_name, guidance, predicted_class)
            return send_file(pdf_filename, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}", 500

def generate_guidance(predicted_class):
    guidance_map = {
        1: (
            "Focus on improving your study habits. Allocate consistent hours daily and review your notes regularly.\n"
            "Here are some actionable steps:\n"
            "- Create a structured daily schedule for study and breaks.\n"
            "- Join study groups to enhance collaborative learning.\n"
            "- Seek help from teachers or tutors for difficult topics.\n"
            "- Reduce distractions by setting up a dedicated study space."
        ),
        2: (
            "Good work! Keep practicing additional sample papers to strengthen your preparation.\n"
            "Additional tips for further improvement:\n"
            "- Review mistakes from previous tests to avoid repeating them.\n"
            "- Increase focus on time management during tests.\n"
            "- Explore advanced resources to challenge yourself.\n"
            "- Maintain a healthy balance between study and relaxation."
        ),
        3: (
            "Excellent performance! Consider helping peers to reinforce your understanding \n and improve leadership skills.\n"
            "Suggestions to excel further:\n"
            "- Take on challenging projects or competitions.\n"
            "- Mentor others to solidify your knowledge.\n"
            "- Stay updated with new developments in your field of interest.\n"
            "- Keep a journal to track your progress and set new goals."
        ),
        4: "You're showing promising signs. \n Strengthen consistency in studies and practice to climb higher.",
        5: "Steady progress! Now focus on identifying weak spots \n and reinforcing them with targeted learning.",
        6: "Great momentum! You're on track. \n  Push a bit further with mock tests and time-bound practice.",
        7: "Strong preparation! Stay sharp \n and review core concepts to ensure long-term retention.",
        8: "Well done! Consider focusing on real-world applications \n and higher-order problem-solving.",
        9: "Outstanding! Prepare for excellence with deep-dive reviews \n and challenge yourself with competitions.",
        10: "Exceptional! You’re a top performer. \n Keep innovating, guiding others, and staying ahead with curiosity."
    }
    return guidance_map.get(predicted_class, "Maintain a balanced approach to your studies and extracurricular activities.")

def generate_pdf(student_name, guidance, predicted_class):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = os.path.join(REPORTS_DIR, f"student_report_{timestamp}.pdf")

    c = canvas.Canvas(pdf_filename)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, f"Student Performance Report for {student_name}")

    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Predicted Performance Level: {predicted_class}")

    text = c.beginText(100, 650)
    text.setFont("Helvetica", 12)
    text.setLeading(14)
    text.textLines(f"Personalized Guidance:\n{guidance}")
    c.drawText(text)

    text = c.beginText(100, 400)
    text.setFont("Helvetica", 12)
    text.setLeading(14)
    text.textLines(
        "Motivational Insights:\n"
        "- Success is a journey, not a destination. Stay consistent in your efforts.\n"
        "- Remember to celebrate small achievements along the way.\n"
        "- Challenges are opportunities to grow and improve. Embrace them with confidence.\n"
        "- Stay curious and keep learning beyond academics."
    )
    c.drawText(text)

    c.setFont("Helvetica", 12)
    c.drawString(100, 150, "Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    c.save()
    return pdf_filename

if __name__ == "__main__":
    app.run(debug=True)
