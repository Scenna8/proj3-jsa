FROM python:3
LABEL maintainer="Jack Abram <jabram@uoregon.edu>"
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["flask_vocab.py"]
