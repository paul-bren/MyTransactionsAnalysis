FROM python:3.11
WORKDIR /app
COPY app_2.py .
COPY requirements.txt .
RUN mkdir templates
COPY templates /app/templates
RUN mkdir static
COPY forms.py /app/forms.py
COPY RegistrationForm.py /app/RegistrationForm.py
COPY static /app/static
RUN mkdir data_2_examine
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app_2.py"]
EXPOSE 8090

