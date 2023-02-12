FROM python:3.11
WORKDIR /app
COPY app_1.py .
COPY requirements.txt .
RUN mkdir templates
COPY templates /app/templates
RUN mkdir static
COPY static /app/static
RUN mkdir data_2_examine
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app_1.py"]
EXPOSE 8090

