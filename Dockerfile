FROM python:3

ENV PATH /opt/conda/bin:$PATH
RUN curl -L https://repo.continuum.io/miniconda/Miniconda3-py38_4.8.2-Linux-x86_64.sh -o miniconda.sh &&  \
sh miniconda.sh -b -p /opt/conda && \
/opt/conda/bin/conda clean -tipsy && \
ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
echo "conda activate base" >> ~/.bashrc && \
echo 'export PATH=/opt/conda/bin:$PATH' >>  ~/.bashrc && \
/bin/bash -c "source ~/.bashrc"
COPY env.yml .
RUN conda env create -f env.yml
WORKDIR /app
ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000
CMD conda run -n openforcefield python app.py