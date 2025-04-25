FROM python:3.11-slim

WORKDIR /app


COPY solve_and_submit.py .
COPY wait-for-it.sh /app/wait-for-it.sh


RUN chmod +x /app/wait-for-it.sh

RUN pip install requests cryptography


CMD ["/app/wait-for-it.sh", "vef-api:8000", "--", "python", "solve_and_submit.py"]

