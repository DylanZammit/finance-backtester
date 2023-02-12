FROM python:3.8

COPY app/requirements.txt /
RUN pip install -r requirements.txt

# copy after pip install to cache previous
COPY app /

ENV FLASK_APP=hello
EXPOSE 8050
CMD python main.py
