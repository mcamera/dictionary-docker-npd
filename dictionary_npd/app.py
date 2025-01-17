 # -*- coding: utf-8 -*-
from flask import Flask, request, render_template
import os
import sys
import json
import pandas as pd
import re
from pymongo import MongoClient
from bson.objectid import ObjectId

project_root = os.path.dirname(__file__)
template_path = os.path.join(project_root, '/dictionary_npd/templates/')
pathSave = './dictionary_npd/file/'

app = Flask(__name__, template_folder=template_path)

def pymongo_python_sys():
        """Função para conexão com o MongoDB
        Args: 
            None
        Returns: 
            object: Mongo conectado no banco de dados
        """

        client = MongoClient('mongodb')
        mongo = client.dictionaryDB
        return mongo

db = pymongo_python_sys()

@app.route('/')
def index():
        """Renderização do template inicial
        Args: 
            None
        Returns: 
            template: index.html
        """

        return render_template('index.html')

#Listagem de diconarios do banco
@app.route('/dictionary')
def dictionary():
        """Busca e listagem dos nomes dos dicionários no banco de dados
        Args: 
            None
        Returns: 
            template: dictionary.html
        """
        dic = db.collection_names(include_system_collections=False) #Incluir select para buscar todos os dicionarios no banco.
        dictionarys = []
        
        for i in dic:
                dictionarys.append(i)
        
        return render_template('dictionary.html', dictionarys=dictionarys)

#Insercao das variaveis e criacao do dicionario no banco
@app.route('/teste', methods=['POST', 'GET']) 
def teste():
        """Criação do dicionario e inserção das variáveis no banco de dados
        Args: 
            None
        Returns: 
            template: dictionary.html
        """
        nameDictionary = str(request.form.get('nameDictionary'))
        variables = str(request.form.get('result'))
        
        if nameDictionary == "None":
                nameDictionary = str(request.values.get('nameDictionary_add'))

        variables  = variables.replace("'",'"').replace('--,','--').split('--')
        nameDictionary = nameDictionary.replace(" ", "_")
        nameDictionary = re.sub("\W", "", nameDictionary)       
        
        for var in variables:
                if var is not '':
                        try:
                                var = var.replace(",}","}")
                                var = json.loads(var)
                        except:
                                return "erro"+var
                        collection = db[nameDictionary]
                        collection.insert(var) 

        dic_submit = db.collection_names(include_system_collections=False) #Incluir select para buscar todos os dicionarios no banco.
        dics_submit = []
        
        for i in dic_submit:
                dics_submit.append(i)
           
        return render_template('dictionary.html', dictionarys=dics_submit)

#Update de uma variavel no banco
@app.route('/update', methods=['POST'] )
def update():
        """Atualização de uma variável no banco de dados
        Args: 
            None
        Returns: 
            template: variables.html
        """
        nameDic_update = str(request.form.get('nameDictionary_up'))
        variable_update = str(request.form.get('result'))
        id_update = str(request.form.get('id_var'))

        try:
                variable_update  = variable_update.replace("'",'"').replace('-', '').replace(",}","}")
                variable_update = json.loads(variable_update)
        except:
                return "Oops! You forgot to add the variable"

        db[nameDic_update].update({'_id': ObjectId(id_update)}, {'$set': variable_update }, upsert = True)
        db_update_list = list(db[nameDic_update].find())
        variable_count = db[nameDic_update].count()
        list_cat = []
        
        for cat in db_update_list:
                d = cat['categories']
                d = {int(k):v for k,v in d.items()}
                d = {k: v for k,v  in sorted(d.items(), key=lambda item: item)}
                list_cat.append(d)

        return render_template('variables.html', dict = nameDic_update, variables = db_update_list, total_variable = variable_count, cat=list_cat)

#Criacao do dicionario em csv para padronizacao
@app.route('/to_csv', methods=['POST'])
def pandas_to_csv():
        """Criação do dicionário em csv formato para a padronização
        Args: 
            None
        Returns: 
            template: index.html
        """
        nameDictionary_csv = str(request.values.get('id'))
        collection = db[nameDictionary_csv]
        df = pd.DataFrame(list(collection.find()))
        df = df[['variable','type', 'categories_std']]
        _count = collection.count()

        characterMap = {u'\u00E7': 'c', u'\u00C7' : 'C', u'\u011F' : 'g', u'\u011E' : 'G', 
        u'\u00F6': 'o', u'\u00D6' : 'O', u'\u015F' : 's', u'\u015E' : 'S', u'\u00FC' : 'u', 
        u'\u00DC' : 'U' , u'\u0131' : 'i', u'\u0049' : 'I', u'\u0259' : 'e', u'\u018F' : 'E'}

        def ascii_pd (df, lista):
                for i in lista:
                        df[i] = (df[i].astype("str")
                                .str.rstrip()
                                .replace(characterMap, regex=True)
                                .str.normalize('NFKD')
                                .str.encode('ascii', errors='ignore')
                                .str.decode('utf-8'))

        ascii_pd(df, ['variable','type', 'categories_std'])

        for cat in range(_count):
                if str(df['categories_std'][cat]) == '{}':
                        df['categories_std'][cat] =str(df['categories_std'][cat])
                        df['categories_std'][cat] = None

        path_csv = (pathSave+nameDictionary_csv+'.csv')
        df.to_csv(path_csv,index=False, header=False, encoding='ascii')
        
        return render_template('index.html')

#Abrir tela de edicao de um dicionario, com listagem das variaveis
@app.route("/edit_dictionary", methods=['GET', 'POST'])
def edit_dictionary():
        """Renderizar a tela de edição de um dicionário com a lista das variáveis
        Args: 
            None
        Returns: 
            template: variables.html
        """
        nameDictionary_edit = str(request.values.get('id'))
        db_edit = db[nameDictionary_edit]
        db_edit_list = list(db_edit.find())
        variable_count = db_edit.count()

        list_cat = []
        for cat in db_edit_list:
                try:
                        d = cat['categories']
                        d = {int(k):v for k,v in d.items()}
                        d = {k: v for k,v  in sorted(d.items(), key=lambda item: item)}
                        list_cat.append(d)
                except:
                        d = {''}
                        list_cat.append(d)

        return render_template('variables.html', dict = nameDictionary_edit, variables = db_edit_list, total_variable = variable_count, cat=list_cat)

#Fazer uma pesquisa de dicionarios no banco
@app.route("/search")
def search():
        """Realizar uma pesquisa dos dicionários no banco de dados
        Args: 
            None
        Returns: 
            template: dictionary.html
        """
        nameDictionary_search = str(request.args.get('dictionary'))
        analise = re.compile(nameDictionary_search)
        collection = db.collection_names(include_system_collections=False)
        search_dic = []
        
        for i in collection:
                if analise.search(i):
                        search_dic.append(i)
        
        return render_template('dictionary.html', dictionarys = search_dic)

#Deletar completamente o dicionario no banco
@app.route('/dictionary_delete', methods=['GET', 'POST'])
def dictionary_delete():
        """Deletar completamente o dicionário no banco de dados
        Args: 
            None
        Returns: 
            template: dictionary.html
        """
        nameDictionary_delete = str(request.values.get('id'))
        collection = db[nameDictionary_delete]
        collection.drop()
        dic = db.collection_names(include_system_collections=False) #Incluir select para buscar todos os dicionarios no banco.
        dictionarys = []
        
        for i in dic:
                dictionarys.append(i)
        
        return render_template('dictionary.html', dictionarys=dictionarys)

#Deletar uma variavel na colecao
@app.route('/variable_delete', methods=['GET', 'POST'])
def variable_delete():
        """Deletar uma variável no dicionário
        Args: 
            None
        Returns: 
            template: variables.html
        """
        name_variable_delete = str(request.values.get('id')).split()
        col_var_del = db[name_variable_delete[0]].remove( { '_id': (ObjectId(name_variable_delete[1])) }, 1)
        db_edit_del = db[name_variable_delete[0]]
        db_edit_list_del = list(db_edit_del.find())
        variable_count = db_edit_del.count()
        list_cat = []
        
        for cat in db_edit_list_del:
                d = cat['categories']
                d = {int(k):v for k,v in d.items()}
                d = {k: v for k,v  in sorted(d.items(), key=lambda item: item)}
                list_cat.append(d)
        
        return render_template('variables.html', dict = name_variable_delete[0], variables = db_edit_list_del, total_variable = variable_count, cat=list_cat)

#Acessar pagina para edicao de variavel
@app.route('/edit_variable', methods=['GET', 'POST'])
def edit_variable():
        """Renderização da pagina de edição de uma variável
        Args: 
            None
        Returns: 
            template: edit.html
        """
        name_variable_edit = str(request.values.get('id')).split()
        col_var_edit =  list(db[name_variable_edit[0]].find({'_id': ObjectId((name_variable_edit[1])) }))
        
        return render_template('edit.html', dict = name_variable_edit[0], vars = col_var_edit)

#Acessar pagina para adicionar novas variaveis
@app.route('/add_variable', methods=['GET', 'POST'])
def add_variable():
        """Renderização da pagina para incluir novas variáveis no dicionário
        Args: 
            None
        Returns: 
            template: add.html
        """
        name_dic_add = str(request.values.get('id'))
        
        return render_template('add.html', dict=name_dic_add)

#Incluir dicionario atraves de arquivo csv
@app.route('/send_csv', methods=['GET', 'POST'])
def send_csv():
        """Incluindo dicionário no banco de dados através de arquivo csv
        Args: 
            None
        Returns: 
            template: dictionary.html
        """
        nameDictionary = str(request.form.get('nameDictionary'))
        csv = str(request.values.get('file_csv'))
        nameDictionary = nameDictionary.replace(" ", "_")
        nameDictionary = re.sub("\W", "", nameDictionary)
        df = pd.read_csv(csv) #csv file which you want to import
        _dic = {}
        
        for item in range(len(df.count())):
                df.categories[item] = _dic
                df.categories_std[item] = _dic
       
        records_ = df.to_dict(orient = 'records')
        collection = db[nameDictionary]               
        collection.insert(records_)
        dic_submit = db.collection_names(include_system_collections=False) #Incluir select para buscar todos os dicionarios no banco.
        dics_submit = []
        
        for i in dic_submit:
                dics_submit.append(i)
           
        return render_template('dictionary.html', dictionarys=dics_submit)   

@app.route('/to_csv_final', methods=['POST'])
def to_csv_final():
        """Criação do dicionário em csv formato para os pesquisadores
        Args: 
            None
        Returns: 
            template: index.html
        """
        nameDictionary_csv = str(request.values.get('id'))

        collection = db[nameDictionary_csv]

        df = pd.DataFrame(list(collection.find()))

        _count = collection.count()

        df = df[['variable','description','type','categories', 'external_comment']]
        path_csv = (pathSave+nameDictionary_csv+'_researcher_version.csv')
        null = None


        characterMap = {u'\u00E7': 'c', u'\u00C7' : 'C', u'\u011F' : 'g', u'\u011E' : 'G',
        u'\u00F6': 'o', u'\u00D6' : 'O', u'\u015F' : 's', u'\u015E' : 'S', u'\u00FC' : 'u',
        u'\u00DC' : 'U' , u'\u0131' : 'i', u'\u0049' : 'I', u'\u0259' : 'e', u'\u018F' : 'E', u'\u007E': '~',
        u'\u0021' : '!', u'\u0022' : '"', u'\u002D' : '-', u'\u00C0' : 'A', u'\u00E3' : 'a', u'\u00E7' : 'c',
        u'\u00E9' : 'e', u'\u00AA':'a', u'\u0040':'a', u'\u00B0':'o', u'\u00BA':'0', u'\u00EA':'e', u'\u00CA':'E'}

        def utf8_pd (df, lista):
                for i in lista:
                        df[i] = (df[i].astype("str")
                                .str.rstrip()
                                .replace(characterMap, regex=True)
                                .str.normalize('NFKC')
                                .str.encode('utf-8', errors='ignore')
                                .str.decode('utf-8'))


        for cat in range(_count):
                if str(df['categories'][cat]) == '{}':
                        df['categories'][cat] = str(df['categories'][cat])
                        df['categories'][cat] = None
                else:
                        try:
                                df['categories'][cat] = {int(k):v for k,v in df['categories'][cat].items()}
                                df['categories'][cat] = {int(k): v for k,v  in sorted(df['categories'][cat].items(), key=lambda item: item)}
                                df['categories'][cat] = str(df['categories'][cat]).replace(':', '-').replace('{', '').replace('}', '').replace("u'", "").replace(',', '\n').replace("'", "").replace('"', '')
                                df['categories'][cat] = "0- Nulo \n"+df['categories'][cat]+"\n 99-Inconsistencia"
                        except:
                                df['categories'][cat] = str(df['categories'][cat]).replace(':', '-').replace('{', '').replace('}', '').replace("u'", "").replace(',', '\n').replace("'", "").replace('"', '')
			        df['categories'][cat] = "0- Nulo \n"+df['categories'][cat]+"\n 99-Inconsistencia"


        utf8_pd(df, ['categories'])
        
        df.to_csv(path_csv,index=False, header=True, encoding='utf8')
        return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)