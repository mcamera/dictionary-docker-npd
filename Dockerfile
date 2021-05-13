FROM python:2.7

# Install requirements
COPY ./requirements.txt ./requirements.txt
RUN pip --no-cache-dir install -r requirements.txt 

COPY ./dictionary_npd /dictionary_npd

CMD python ./dictionary_npd/app.py