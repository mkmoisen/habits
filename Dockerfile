FROM mkmoisen/habits:base

WORKDIR /app/habits/habits

COPY . .

CMD ["gunicorn", "habits.app:create_app()", "--workers=1", "--threads=4", "--bind", "0.0.0.0:80"]
