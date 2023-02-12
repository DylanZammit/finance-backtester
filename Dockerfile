FROM python:3.8

# install app dependencies
# RUN apt-get update && apt-get install -y python3 python3-pip

COPY app /
# WORKDIR app

RUN pip install -r requirements.txt

# final configuration
ENV FLASK_APP=hello
EXPOSE 8050
CMD python main.py
