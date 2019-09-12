#!/usr/bin/env python
# coding: utf-8

# In[1]:


from __future__ import unicode_literals, print_function
import random
from pathlib import Path
import spacy
from spacy import displacy
from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex,minibatch, compounding
import re
from collections import Counter
import en_core_web_sm
from pprint import pprint
from spacy.matcher import Matcher
from spacy.tokens import Span
from spacy.matcher import PhraseMatcher
import unidecode 
import string
from datetime import datetime
import os
import pandas as pd


# In[2]:


def meta(file):
    print('Identification number:',id_num(file))
    print('Agenda item:',agenda_item(file))
    print('Title:',title(file))
    print('Approval date:',approval_date(file))
    print('Session:',session(file))
    print('Proponent authority:',proponent_authority(file))
    print('Closing formula:',closing_formula(file)) 


# In[4]:


nlp = spacy.load("en_core_web_sm")
infixes = nlp.Defaults.prefixes + ( r"[-]~",r'[/]~',r'\.')
infix_re = spacy.util.compile_infix_regex(infixes)
def custom_tokenizer(nlp):
    return Tokenizer(nlp.vocab, infix_finditer=infix_re.finditer)

nlp.tokenizer = custom_tokenizer(nlp)


# In[5]:


def seg(attr,file,nlp=nlp):  #return spacy span
    if attr=='pre':
        return preamble(file,nlp)
    if attr=='op':
        return operative(file,nlp)
    if attr=='ax':
        return annex(file)
    if attr=='fn':
        return footnote(file)


# In[6]:


def convert(path):
    word = wc.Dispatch('Word.Application')
    doc = word.Documents.Open(path)  
    doc.SaveAs(path+'.docx', 12) 
    doc.SaveAs(path+'.txt',4)
    d = Document(path+'.docx') 
    if d.tables!=[]:
        print(d.tables)
    doc.Close()
    word.Quit()
    return path+'.txt'


# In[7]:


def read(path):
    #path_txt=convert(path)
    file=open(path,'r')
    file1=file.read()
    file2=unidecode.unidecode(file1)
    file.close()
    return file2


# In[ ]:





# In[8]:


def abbr(file,nlp=nlp):
    return nlp(extract(file))
    


# In[9]:


def refered_doc(file,df,get_list=True):
    df=df.set_index(df['doc'])
    refer_list=reference(file)
    if refer_list==[]:
        return None
    else:
        result=[]
        lst=' '.join(refer_list)
        pa=re.compile('\d+/\d+')
        w=re.findall(pa,lst)
        for i in w:
            try:
                ele=(df[df['ID']==('A/RES/'+i)].index.values[0])
                result.append(ele)
            except:
                pass
        if not get_list:
            return ' '.join(result)
        else:
            return result


# In[10]:


# lst=[]
# for idx in df.index:
#     try:
#         file=read(r'D:\UN\txt\txt\\'+idx+'.DOC.txt')
#     except:
#         print(idx)
#         file=read(r'D:\UN\txt\txt\\'+idx+'.DOCX.txt')
#     lst.append(refered_doc(file,df))
    
        


# In[11]:


# topic_cluster(r'D:\UN\refined.xlsx')


# In[12]:


def topic_cluster(df,cate=None,keyword=None,topic_number=5,MAX_DOCUMENT=2000,show_freq=False,term_number=30,random_state=0):
    
    
    import gensim
    from gensim import corpora
    import pyLDAvis
    import pyLDAvis.gensim
    from nltk import FreqDist
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    def freq_words(x, terms = term_number):
        all_words = ' '.join([text for text in x])
        all_words = all_words.split()

        fdist = FreqDist(all_words)
        words_df = pd.DataFrame({'word':list(fdist.keys()), 'count':list(fdist.values())})

       
        d = words_df.nlargest(columns="count", n = terms) 
        plt.figure(figsize=(30,5))
        ax = sns.barplot(data=d, x= "word", y = "count")
        ax.set(ylabel = 'Count')
        plt.show()
        
    MAX_DOCUMENT=max(len(df),MAX_DOCUMENT)
    print('Reading...')
    
    if cate:
        data=df[df['Category']==cate]
        
    elif keyword:
        data=filter_keyword(keyword,df)

    else:
        data=df.tail(MAX_DOCUMENT)
    data['text']=data["Preamble"].map(str) + data["Operative"].map(str)+data["Title"].map(str)
    data['text'] = data['text'].str.replace("[^a-zA-Z#]", " ")
    
    from nltk.corpus import stopwords
    stop_words = stopwords.words('english')
    
    def remove_stopwords(rev):
        rev_new = " ".join([i for i in rev if i not in stop_words])
        return rev_new
    
    data['text'] = data['text'].apply(lambda x: ' '.join([w for w in x.split() if len(w)>3]))
    reviews = [remove_stopwords(r.split()) for r in data['text']]
    reviews = [r.lower() for r in reviews]
    
    def lemmatization(texts, tags=['NOUN', 'ADJ']): # filter noun and adjective
        output = []
        for sent in texts:
            doc = nlp(" ".join(sent)) 
            output.append([token.lemma_ for token in doc if token.pos_ in tags])
        return output
    
    print('Lemmatizing...')
    tokenized_reviews = pd.Series(reviews).apply(lambda x: x.split())
    reviews_2 = lemmatization(tokenized_reviews)
    
    print('Creating dictionary...')
    reviews_3 = []
    for i in range(len(reviews_2)):
        reviews_3.append(' '.join(reviews_2[i]))

    data['text']=reviews_3

    if show_freq:
        freq_words(data['text'],30)
    
    dictionary = corpora.Dictionary(reviews_2)
    print('LDA modeling...')
    doc_term_matrix = [dictionary.doc2bow(rev) for rev in reviews_2]
    LDA = gensim.models.ldamodel.LdaModel
    lda_model = LDA(corpus=doc_term_matrix,
                                       id2word=dictionary,
                                       num_topics=topic_number, 
                                       random_state=random_state,
                                       chunksize=1000,
                                       passes=50)
    return lda_model,doc_term_matrix,dictionary

        


# In[13]:


def wordcount(file,terms):
    from nltk import FreqDist
    df=pd.read_excel('backup.xlsx')
    df=df.set_index(df['doc'])
    x=df.loc[file,'text']
    all_words = x.split()

    fdist = FreqDist(all_words)
    words_df = pd.DataFrame({'word':list(fdist.keys()), 'count':list(fdist.values())})


    d = words_df.nlargest(columns="count", n = terms) 
    return d


# In[14]:


# wordcount('N0946843',10)


# In[15]:


def filter_keyword(word,f,t=1,p=1,o=1,case_sensitive=True):
    f=f.fillna('xxxxxxxxxx')
    if not case_sensitive:
        word=word.upper()
        df=f.apply(lambda x: x.astype(str).str.upper())
        
    else:
        df=f
    if p==1:
        t1=df[df['Preamble'].str.contains(word)]
    else:
        t1=pd.DataFrame()
    if o==1:
        t2=df[df['Operative'].str.contains(word)]
    else:
        t2=pd.DataFrame()
    if t==1:
        t3=df[df['Title'].str.contains(word)]
    else:
        t3=pd.DataFrame()
    t=pd.concat([t1,t2,t3]).drop_duplicates()

    if not case_sensitive:
        return f.loc[t.index]
    else:
        return t
        
    
    


# In[16]:


# filter_keyword('sustain',df,case_sensitive=False)


# In[17]:


# pyLDAvis.enable_notebook()
# pyLDAvis.gensim.prepare(*topic_cluster())  


# In[18]:


def session(file):
    try:
        doc=nlp(file)
        matcher = Matcher(nlp.vocab)
        pattern = [{},{'ORTH': 'session'}, {'IS_SPACE': True}]
        matcher.add('session', None, pattern)
        matches = matcher(doc)
        spans = [(ent_id, doc[start : end-1]) for ent_id, start, end in matches]
        return spans[0][1]
    except:
        return 0

def approval_date(file):
    try:
        start=file.find('adopted by the General Assembly on')
        if start!=-1:
            end=file[start:].find('\n')
            item=file[start:start+end]
            date=nlp(item)[6:]
        else:
            start=file.find('plenary meeting')
            start2=file[start:].find('\n')
            item=file[start+start2:]
            item=str(nlp(item)[:4]).strip()
            date=nlp(item)
        d = datetime.strptime(str(date), '%d %B %Y')
        return d.strftime('%Y-%m-%d')
    except:
        return 0

def id_num(file):
    try:
        doc=nlp(file)
        pattern=re.compile(r'A/RES/\d+/\d+.+')
        for match in re.finditer(pattern, doc.text):
            start, end = match.span()
            num=doc.text[start:end]
        return num
    except:
        return 0

    
def proponent_authority(file):
    try:
        org=[]
        start=file.find('on the report of')
        if start!=-1:
            end=file[start:].find('\n')
            item=file[start:start+end]
            for entity in nlp(item).ents:
                if entity.label_=='ORG':
                    org.append(entity.text)
            return ' '.join(org)
        else:
            return 'plenary'   
    except:
        return 0
    
def agenda_item(file):
    try:
        start=file.find('Agenda item')
        end=file[start:].find('\n')
        item=file[start:start+end]
        return nlp(item)[2:]
    except:
        return 0

def title(file):
    try:
        en=file.find('The General Assembly,')
        doc=nlp(file[:en])
        pattern=re.compile('\d+/\d+\.')
        match=re.search(pattern,doc.text)
        start,end=match.span()
        title=str(list(nlp(doc.text[end:]).sents)[0]).strip()
        return title
    except:
        return 0

def annex(file):
    try:
        file=file[:file.rfind('[')]
        start=file.find('Annex')
        if start==-1:
            return None
        else:
            try:
                tfile=file[start:]
                pattern=re.compile('[\t|\n]1(\s)(\t)?[A-Z].+\.')
                match=re.search(pattern, tfile)
                return nlp(tfile[:match.span()[0]])
            except:
                return nlp(file[start:])
    except:
        return 0
    
def preamble(file,nlp=nlp):
    try:
        idx=file.find('The General Assembly,')
        if idx!=-1:
            file=file[idx+len('The General Assembly,'):]
        else:
            file=file[file.find('The General Assembly\n')+len('The General Assembly,'):]
        pattern=re.compile('[A-Z][a-z]+')
        match = pattern.search(file)
        if str(file[match.span()[0]:match.span()[1]])[-1]=='s':
            return nlp(' ')
        else:
            pattern=re.compile('[\s\S]*,(\d+)?(\s+)?\n')
            match=pattern.search(file)
            return nlp(file[:match.span()[1]+1])
    except:
        return nlp(' ')
    
def operative(file,nlp=nlp):
    try:
        idx=file.find('The General Assembly,')
        if idx!=-1:
            file=file[idx+len('The General Assembly,'):]
        else:
            file=file[file.find('The General Assembly\n')+len('The General Assembly,'):]

        pattern=re.compile('^Annex') 
        idx=pattern.search(file)
        if idx is not None:
            file=file[:idx.start()]
        file=file[:file.rfind('plenary meeting')]

        file=file[:file.rfind('.')+1]
        pattern=re.compile('\t1\.(\s|\t)')
        match=pattern.search(file)

        if match is not None:
            sep2=match.span()[0]
            if sep2!=-1:
                idx=file[:sep2].rfind('I\n')
                if idx!=-1:
                    return nlp(file[idx:])
                doc=nlp(file[sep2-1:])
            else:
                pattern=re.compile('[\s\S]*,(\d+)?(\s+)?\n')
                match=pattern.search(file)
                file=file[match.span()[1]:]
                pattern2=re.compile('[A-Z][a-z]+s')
                match=pattern.search(file)
                doc=nlp(file[match.span()[0]:])
            return doc
        else:

            pattern=re.compile('\t[A-Z][a-z]+s(\s|,)')
            return nlp(file[pattern.search(file).span()[0]:])
    except:
        return 0


def closing_formula(file):
    try:
        if 'Annex' in file:
            mark=file.find('Annex')
            if file[:mark].rfind('plenary meeting')!=-1:
                file = file[:mark]
                mark = file.rfind('plenary meeting')
            else:
                mark=file.rfind('plenary meeting')
        else:
            mark=file.rfind('plenary meeting')
            start=file[:mark].rfind('\n')
            doc=nlp(file[start+1:])
            matcher = Matcher(nlp.vocab)
            pattern = [{'IS_DIGIT':True},{'IS_TITLE':True}, {'IS_DIGIT': True}]
            matcher.add('date', None, pattern)
            matches = matcher(doc)
            spans = [(ent_id,doc[:end]) for ent_id, start, end in matches][0][1]
        return spans
    except:
        return 0
    
    
             
def footnote(file):   # ** unrecognize file 4
    try:
        file=file[:file.rfind('[')]
        file=file[file.find('plenary meeting'):]
        doc=nlp(file)
        matcher = Matcher(nlp.vocab)
        pattern = [{'IS_DIGIT':True},{'IS_TITLE':True}, {'IS_DIGIT': True}]
        matcher.add('date', None, pattern)
        matches = matcher(doc)
        spans = [(ent_id,doc [end+1:]) for ent_id, start, end in matches][0][1]
        start=str(spans).find('Annex')
        if start==-1:
            return spans
        else:
            try:
                pattern=re.compile('[\t|\n]1(\s)(\t)?[A-Z].+\.') ##file8 
                match=pattern.search(file)
                return nlp(file[match.span()[0]:])
            except:
                return None
    except:
        return 0


# In[19]:


def reference(file): 
    try:
        reference=[]
        doc=preamble(file)
        matcher = Matcher(nlp.vocab)
        pattern=[{'ORTH':{'IN':['resolution','resolutions','decision','decisions']}},
                 {'TEXT':{'REGEX':'(\d+/\d+\s[A-Z]\s)|([A-Z]+/\d+)|(\d+/\d+)|(\d+)'}},
                 {'ORTH':{'IN':['A','B','C','D','E']},'OP':'?'}]
        matcher.add('citation',None, pattern)
        matches = matcher(doc)
        spans = [(start,(doc[start:end])) for ent_id, start, end in matches]
        for (start,i) in spans:
            if str(i[0])=='resolutions' or str(i[0])=='decisions':
                pattern2=re.compile(',([^a-zA-Z]+)?\n')
                end=pattern2.search(doc[start+1:].text).span()[1]
                doc2=(doc[start+1:].text)[:end]
                an_re=doc2.find('resolution')
                an_de=doc2.find('decision')
                if an_re==-1 and an_de==-1:
                    pass
                elif an_re==-1 or an_de==-1:
                    doc2=doc2[:max(an_re,an_de)]
                else:
                    doc2=doc2[:min(an_re,an_de)]
                cites=[]
                found=re.findall(re.compile('(\d+/\d+\s[A-Z]\s)|([A-Z]+/\d+)|(\d+/\d+)|(\d+[^a-z\n,]+[(])'),doc2)
                for w in found:
                    c=[i for i in w if str(i)!=''] 
                    if c[0][-1]=='(':
                        c[0]=c[0][:-1]
                    cites.append(c[0])
                cite=str(i[0])+' '+' '.join(cites)
                reference.append(nlp(cite))
            else:
                reference.append(i)
        return list(set([str(x) for x in reference]))
    except:
        return 0


# In[20]:


def places(file):   ##x 6 aff need trainig
    try:
        pre_loc,op_loc=[],[]
        pre=preamble(file)
        for entity in pre.ents:
            if entity.label_=='GPE':
                print(entity.text)
                if entity.text[0].isdigit() or entity.text=='States':
                    continue
                text=entity.text.rstrip(string.digits)
                pre_loc.append(text)
        op=operative(file)
        for entity in op.ents:
            if entity.label_=='GPE':
                if entity.text[0].isdigit() or entity.text=='States':
                    continue
                text=entity.text.rstrip(string.digits)
                op_loc.append(entity.text)
        return pre_loc,op_loc
    except:
        return 0,0


# In[21]:


def org(file,nlp=nlp):  
    try:
        pre_loc,op_loc=[],[]
        pre=preamble(file,nlp)
        for entity in pre.ents:
            if entity.label_=='ORG':
                if entity.text[0].isdigit() or entity.text=='States':
                    continue
                text=entity.text.rstrip(string.digits)
                pre_loc.append(text)
        op=operative(file,nlp)
        for entity in op.ents:
            if entity.label_=='ORG':
                if entity.text[0].isdigit() or entity.text=='States':
                    continue
                text=entity.text.rstrip(string.digits)
                op_loc.append(entity.text)
        return pre_loc,op_loc
    except:
        return 0


# In[22]:


def future_date(file,nlp=nlp):   
    try:
        approval=approval_date(file)
#         approval=date
        doc=operative(file,nlp)
        def get_date(doc=doc):
            spans=[]
            matcher = Matcher(nlp.vocab)
            pattern = [{'IS_DIGIT':True,'OP':'?'},{'IS_TITLE':True,'OP':'?'},{'ORTH':'to','OP':'?'},
                       {'IS_DIGIT':True},{'IS_TITLE':True}, {'IS_DIGIT': True}]
            matcher.add('date', None, pattern)
            matches = matcher(doc)
            for ent_id, start, end in matches:
                if end-start !=4:
                    if end-start==5 and str(doc[start]).isdigit() and len(str(doc[start]))<3:
                        span=' '.join([str(doc[start]),str(doc[start+3]),str(doc[start+4])])
                    elif end-start==6:
                        span=' '.join([str(doc[start]),str(doc[start+1]),str(doc[end-1])])
                    elif end-start==3:
                        span=str(doc[start:end])
                    yan=nlp(span)
                    span=' '.join([str(yan[0]),str(yan[1]),str(yan[2])[:4]])    
                    if datetime.strptime(span, '%d %B %Y').strftime('%Y-%m-%d')>=approval:   
                        spans.append(span)    
            return spans

        def get_year(doc=doc):
            spans=[]
            matcher = Matcher(nlp.vocab)
            pattern = [{'IS_TITLE':False}, {'TEXT': {'REGEX':'^(1|2)(0|9)\d\d$'}}]
            pattern2=[{'ORTH':'resolution','OP':'!'},{'TEXT': {'REGEX':'^\d\d\d\d'}}]
            matcher.add('year', None, pattern)
            matches = matcher(doc)
            span=[(start,doc[start+1:end]) for ent_id, start, end in matches]
            for i,(s,y) in enumerate(span):
                try:
                    if not (int(str(y).strip())<datetime.strptime(approval, '%Y-%m-%d').year or 'resolution'in str(doc[s])):
                        spans.append(span[i])
                except:
                    pass
            return [x[1].text for x in spans]


        return list(set(get_date())),list(set(get_year()))
    except:
        return 0


# In[23]:


TRAIN_DATA = [ 
    ('Recalling also its decision 50/500 of 17 September 1996 on the financing of the United Nations Logistics Base at Brindisi, Italy, and its subsequent resolutions thereon, the latest of which was resolution 53/236 of 8 June 1999', { 
     'entities': [ (38, 55, 'DATE'),(76,109,'ORG'),(112,120,'GPE'),(122,127,'GPE'),(215,226,'DATE')] 
    }), 
    ('Having considered the reports of the Secretary-General on the financing of the Logistics Base and the related reports of the Advisory Committee on Administrative and Budgetary Questions', { 
     'entities': [(33, 54, 'PERSON'),(75,93,'ORG'),(121,185,'ORG')] 
    }), 
    ('Recalling its resolutions 54/196 of 22 December 1999, 55/186 and 55/213 of 20 December 2000 and 55/245 A of 21 March 2001, and decision 1/1 of the Preparatory Committee for the International Conference on Financing for Development', { 
     'entities': [(36,52,'DATE'),(75,91,'DATE'),(108,121,'DATE'),(143,168,'ORG'),(173,230,'EVENT')] 
    }), 
    ('Having considered the reports of the Secretary-General on the financing of the United Nations Observer Mission in Georgia1 and the related report of the Advisory Committee on Administrative and Budgetary Questions ',{
     'entities':[(33,54,'PERSON'),(75,110,'ORG'),(114,122,'GPE'),(149,213,'ORG')]
    }),
    ('Recalling Security Council resolution 854 (1993) of 6 August 1993',{
    'entities':[(10,26,'ORG'),(52,65,'DATE')]
    }),
    ('the Council established the United Nations Observer Mission in Georgia',{
    'entities':[(0,11,'ORG'),(24,59,'ORG'),(63,70,'GPE')]
    }),
    ('Having considered the reports of the Secretary-General on the budget performance of the support account for peacekeeping operations for the period from 1 July 2016 to 30 June 2017,1 on the budget for the support account for peacekeeping operations',{
    'entities':[(33,54,'PERSON'),(152,163,'DATE'),(167,179,'DATE'),]
    }),
    ('the report of the Independent Audit Advisory Committee on the proposed budget of the Office of Internal Oversight Services under the support account and the related report of the Advisory Committee on Administrative and Budgetary Questions',{
    'entities':[(14,54,'ORG'),(81,122,'ORG'),(175,239,'ORG')] 
    }),
    ('Reaffirming also its resolution 69/313 of 27 July 2015 on the Addis Ababa Action Agenda of the Third International Conference on Financing for Development, which is an integral part of the 2030 Agenda for Sustainable Development',{
    'entities':[(42,54,'DATE'),(91,154,'EVENT')]
    }),

    ("Reaffirming the pertinent principles and provisions contained in the Charter of Economic Rights and Duties of States proclaimed by the General Assembly in its resolution 3281 (XXIX) of 12 December 1974",{
    'entities':[(65,116,'LAW'),(134,150,'ORG'),(185,201,'DATE')]
    }),
    ('Recalling section XIV of its resolution 49/233 A of 23 December 1994,', { 
     'entities': [(52,68,'DATE')]
    }),
    ("Recognizing that a socially responsible private sector can contribute to the promotion of children's rights and education through relevant initiatives such as the Children's Rights and Business Principles and the Framework for Business Engagement in Education",{
    'entities':[(159,204,'LAW'),(209,259,'LAW')]
    }),
    ("Decides to apportion among Member States the amount of 24,669,100 dollars for the period from 16 October 2006 to 30 June 2007 at a monthly rate of 2,902,247 dollars",{
    'entities': [(55, 73, 'MONEY'),(94,110,'DATE'),(113,125,'DATE'),(147,164,'MONEY')]
    }),
     ("as well as Commission on Human Rights resolution 1998/11 of 9 April 1998,1 and taking note of Commission resolution 2000/11 of 17 April 2000",{
    'entities':[(60,72,'DATE'),(127,140,'DATE')]
    }),
        ('Calls upon all members of the World Trade Organization to conclude negotiations on fisheries subsidies in 2019, consistent with the instructions from the eleventh Ministerial Conference of the World Trade Organization and with a view to meeting the Sustainable Development Goals;',
    {'entities':([26,54,'ORG'],[150,185,'EVENT'],[189,217,'ORG'])
    }),
    ('Takes note of the fourteenth session of the United Nations Conference on Trade and Development, held in Nairobi in July 2016, as well as the outcome of the eleventh Ministerial Conference of the World Trade Organization, held in Buenos Aires from 10 to 13 December 2017, and expresses its appreciation to the Government of Argentina for hosting the meeting;',
    {'entities':([14,94,'EVENT'],[104,111,'GPE'],[115,124,'DATE'],[152,187,'EVENT'],[191,219,'ORG'],[229,241,'GPE'],[242,269,'DATE'],[305,332,'ORG'])
    }),
] 


# In[24]:



def main(model=None, output_dir=None, n_iter=150,labels=None):
    if model is not None:
        nlp = spacy.load(model) 
        print("Loaded model '%s'" % model)
    else:
        nlp = spacy.blank("en")  
        print("Created blank 'en' model")

    # create the built-in pipeline components and add them to the pipeline
    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")
        nlp.add_pipe(ner)
    else:
        ner = nlp.get_pipe("ner")
    
    if labels is not None:
        for label in labels:
            ner.add_label(label)

    if model is None:
        optimizer = nlp.begin_training()
    else:
        optimizer = nlp.resume_training()
    
    move_names = list(ner.move_names)

    # get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):  # only train NER
        sizes = compounding(1.0, 4.0, 1.001)
        # batch up the examples using spaCy's minibatch
        for itn in range(n_iter):
            random.shuffle(TRAIN_DATA)
            batches = minibatch(TRAIN_DATA, size=sizes)
            losses = {}
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(texts, annotations, sgd=optimizer, drop=0.35, losses=losses)
            print("Losses", losses)


    for text, _ in TRAIN_DATA:
        doc = nlp(text)
        print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
        print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])


    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)


        print("Loading from", output_dir)
        nlp2 = spacy.load(output_dir)
        for text, _ in TRAIN_DATA:
            doc = nlp2(text)
            print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
            print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])
    return nlp2

# nlp2=main("en_core_web_sm",r'D:\UN')
# nlp2=main()


# In[25]:


def op_to_sentence(op):

    sents=op.text.split('\n')
    sents=[x for x in sents if x is not None and x !=' 'and x!='']
    sentences=[]
    for sent in sents:
        pattern=re.compile('[A-Z][a-z]+')
        match=pattern.search(sent)
        if match is None:
            continue
        sentence=sent[match.span()[0]:]
        pattern2=re.compile('\s\((.+)\)')
        match2=pattern2.search(sentence)
        if match2 is not None:
            sentence=sentence[:match2.span()[0]]+sentence[match2.span()[1]:]
        sentence=purify(sentence)
        sentence=purify2(sentence)
        sentences.append(sentence)

    return sentences


# In[26]:


def purify(sentence):   
    sentence=sentence.replace('also ','').replace('Also ','').replace('Further ','').replace('further ','')   
    
    begin=sentence.find('in accordance with')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
            
    begin=sentence.find('in order to')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
    
    begin=sentence.find('commensurate with')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
    
    begin=sentence.find('inclusive of')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
    
    begin=sentence.find('including')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
            
    begin=sentence.find('as provided for')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
            
    begin=sentence.find('bearing in mind')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
            
    begin=sentence.find('in respect of')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            if len(nlp(sentence[begin:begin+comma]))<12:
                sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            if len(nlp(sentence[begin]))<12:
                sentence=sentence[:begin]
    
    begin=sentence.find('as well as')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
            
    begin=sentence.find('as set out')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
            
    begin=sentence.find('representing')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
            
    begin=sentence.find('referred to')
    if begin!=-1:
        comma=sentence[begin:].find(',')
        if comma!=-1:
            sentence=sentence[:begin]+sentence[begin+comma+1:]
        else:
            sentence=sentence[:begin]
    
    index=sentence.rfind(';')
    if index!=-1:
        sentence=sentence[:index+1]
        
    pattern=re.compile('\d+,\d+(,)?(\d+)?(,)?(\d+)?')
    for m in pattern.finditer(sentence):
        mm = m.group()
        sentence = sentence.replace(mm,mm.replace(',',''))

    sentence=nlp(sentence)
    


    matcher = Matcher(nlp.vocab)
    pattern=[{'ORTH':{'IN':['of','in']}},
             {'ORTH':{'IN':['its','General']}},
             {'ORTH':'Assembly','OP':'?'},
             {'ORTH':{'IN':['resolution','resolutions']}}]
    matcher.add('refer',None, pattern)
    matches = matcher(sentence)
    if matches !=[]:
        record=[]
        for _,start,end in matches:
            for item in sentence[end:]:
                if item.is_punct:
                    record.append((end,item.i))
                    break
        sent=[str(t) for t in sentence]
        for t in reversed(record):
            del sent[t[0]:t[1]]
        sentence=' '.join(sent)
        return nlp(sentence)
    
    return sentence
    


# In[27]:


def purify2(sentence): 
    matcher=Matcher(nlp.vocab)
    pattern=[{'ORTH':{'IN':['paragraph','paragraphs']}},{'IS_DIGIT':True},
            {'ORTH':'and'},{'IS_DIGIT':True,'OP':'?'}]
    matcher.add('para',None, pattern)
    matches = matcher(sentence)
    if matches!=[]:
        idx,start,end=matches[0]
        temp=str(sentence[:start+1])+' '+str(sentence[end:])
        sentence=nlp(temp)
    
    matcher=Matcher(nlp.vocab)
    pattern2 = [{'ORTH':'from'},{'IS_DIGIT':True,'OP':'?'},{'IS_TITLE':True,'OP':'?'},{'IS_DIGIT':True,'OP':'?'},{'ORTH':'to'},
               {'IS_DIGIT':True,'OP':'?'},{'IS_TITLE':True}, {'IS_DIGIT': True}]
    matcher.add('date', None, pattern2)
    matches=matcher(sentence)
    if matches!=[]:
        idx,start,end=matches[0]
        temp=str(sentence[:start])+' '+str(sentence[end:])
        sentence=nlp(temp)

    matcher=Matcher(nlp.vocab)
    pattern6 = [{'ORTH':'at'},{'IS_DIGIT':True,'OP':'?'},{'IS_TITLE':True},{'IS_DIGIT':True}]
    matcher.add('date', None, pattern6)
    matches=matcher(sentence)
    if matches!=[]:
        idx,start,end=matches[0]
        temp=str(sentence[:start])+' '+str(sentence[end:])
        sentence=nlp(temp)
        
    record=[]
    matcher=Matcher(nlp.vocab)
    pattern3=[{'ORTH':','},{'OP':'+'},{'ORTH':','}]
    matcher.add('charuyu',None,pattern3)
    matches=matcher(sentence)
    if matches!=[]:
        for _,start,end in matches:
            if end-start<=5:
                record.append((start+1,end))
        if record!=[]:
            sent=[str(t) for t in sentence]
            for t in reversed(record):
                del sent[t[0]:t[1]]
            sentence=nlp(' '.join(sent))
    
    record=[]
    matcher=Matcher(nlp.vocab)
    pattern5=[{'ORTH':','},{'IS_DIGIT':True},{'ORTH':'dollars'}]
    matcher.add('charuyu',None,pattern5)
    matches=matcher(sentence)
    if matches !=[]:
        record=[]
        for _,start,end in matches:
            for item in sentence[end:]:
                if item.is_punct:
                    record.append((start+1,item.i))
                    break
        sent=[str(t) for t in sentence]
        for t in reversed(record):
            del sent[t[0]:t[1]]
        sentence=nlp(' '.join(sent))
    
            
    matcher=Matcher(nlp.vocab)
    pattern4=[{'IS_DIGIT':True},{'ORTH':'.'},{'IS_DIGIT':True}]
    matcher.add('num',None,pattern4)
    matches=matcher(sentence)
    if matches!=[]:
        for _, start, end in matches:
            sentence[start:end].merge()
    
    return sentence
    


# In[28]:


def extract(file):
    try:
        op=operative(file)
        sents=op_to_sentence(op)
        result=[]
        for sent in sents:
            childs=[]
            grands=[]
            extragrands=[]
            sons=[]
            babies=[]
            roots = [token for token in sent if token.head == token]
            for token in sent:
                if str(token)=='no':
                    roots.append(token)
                if str(token)=='not':
                    babies.append(token)

            for root in roots:
                for item in root.children:
                    if item.dep_!='punct' and item.pos_!='DET' and item.dep_!='aux' and item.dep_!='mark' and item.dep_!='appos':
                        childs.append(item)

                for child in childs:
                    for item in child.children:
                        if item.dep_!='punct'and item.pos_!='DET'and item.dep_!='aux'and item.dep_!='mark':
                            if str(item)=='comprising':
                                pass
                            else:
                                grands.append(item)

                for grand in grands:
                    for item in grand.children:
                        if item.pos_=='PROPN' or item.pos_=='NOUN'  or item.dep_=='cc'or item.dep_=='ccomp' or item.pos_=='VERB' or item.pos_=='NUM':
                            if str(item)=='period'or str(item)=='amount':
                                grands.remove(grand)
                            elif item.dep_=='advcl':
                                pass
                            else:
                                extragrands.append(item)
                        elif item.pos_=='ADP':
                            for word in item.children:
                                if word.dep_=='pobj':
                                    if sent[word.i-1].pos_=='NUM':
                                        sons.append(sent[word.i-1])
                                        sons.append(word)
                                    if sent[word.i-1].dep_=='compound' and sent[word.i-2].dep_=='compound':
                                        sons.append(sent[word.i-1])
                                        sons.append(sent[word.i-2])
                                        sons.append(word)
                                        extragrands.append(item)
                                    try:
                                        temp=word.nbor().nbor()
                                        if word.is_ancestor(temp) and temp.pos_!='DET':
                                            sons.append(temp)
                                            if temp in temp.head.lefts:
                                                sons.append(temp.head)
                                            else:
                                                sons.append(temp.head.head)
                                            for wd in temp.children:
                                                if wd.dep_=='conj'or wd.dep_=='dobj':
                                                    babies.append(wd)
                                    except:
                                        pass

                        elif str(item)=='of':
                            for word in item.children:
                                if word.pos_=='NOUN':
                                    extragrands.append(item)
                                    sons.append(word)
                                    for wd in word.children:
                                        if wd.dep_=='conj':
                                            sons.append(wd)
                        elif str(item)=='for':
                            for word in item.children:
                                if word.pos_=='NUM':
                                    extragrands.append(item)
                                    sons.append(word)

                for extragrand in extragrands:
                    for item in extragrand.children:
                        if item.pos_=='PROPN' or item.pos_=='NOUN' or item.dep_=='nummod' or item.pos_=='NUM':
                            sons.append(item)
                        if item.pos_=='VERB':
                            for word in item.children:
                                if word.pos_=='NOUN':
                                    sons.append(item)
                                    babies.append(word)
                        if item.dep_=='amod':
                            if item in list(extragrand.lefts):
                                sons.append(item)
                        if str(item)=='of':
                            for word in item.children:
                                if word.pos_=='NOUN'and str(word)!='dollars':
                                    sons.append(item)
                                    babies.append(word)
                                    for wd in word.children:
                                        if wd.dep_=='conj':
                                            babies.append(wd)
                        if str(item)=='on':
                            for word in item.children:
                                if word.pos_=='NOUN':
                                    sons.append(item)
                                    babies.append(word)
                                    for wd in word.children:
                                        if wd.dep=='conj' or wd.dep_=='amod' and wd in list(word.lefts):
                                            babies.append(wd)


            dic={}
            for t in roots+childs+grands+extragrands+sons+babies:
                dic[t]=t.i

            trunk=sorted(dic.items(), key=lambda x: x[1])
            extracted=[t[0].text for t in trunk]

            result.append(' '.join(extracted))
            s=''
            for i in result:
                s+='\t'+i+';\n'
        return s
    except:
        return 0


# In[29]:


# lt=[]
# for i in df['doc']:
#     try:
#         try:
#             file=read(r'D:\UN\txt\txt\\'+i+'.DOC.txt')
#         except:
#             file=read(r'D:\UN\txt\txt\\'+i+'.DOCX.txt')
#         lt.append(extract(file))
#     except:
#         lt.append(0)
    


# In[30]:



# lst=[]
# for ix,i in enumerate(df['Preamble']):

#     try:
#         idx=0
#         while i[idx]=='\n'or i[idx]==' ' or i[idx]=='\t':
#             idx+=1
#         j='\n\t\t'+i[idx:]

#         lst.append(j)
#     except:
#         print(ix,i)
#         lst.append('')


# In[31]:


def classify(path,label,BATCH_SIZE,NUM_EPOCHS=10):
    import tensorflow as tf
    import keras
    from keras.preprocessing.text import Tokenizer
    from keras.preprocessing.sequence import pad_sequences
    import numpy as np
    
    df=pd.read_excel(path)
    
    df=df[['doc','Title','Preamble','Operative',label]]
    df=df.fillna(' ')
    
    train=df[~pd.isnull(df[label])]
    print('number of train:',len(train))
    try:
        test=df[pd.isnull(df[label])]
        print('number of test:',len(test))
    except:
        pass

    
    Train=[]
    Test=[]
    
    print('Find',len(df[label].unique()),'classes')
    
    for lab in df[label].unique():
        a=df[df[label]==lab]
        if len(a)>20:
            test_=a.tail(int(len(a)*0.2))
            train_=a.head(len(a)-int(len(a)*0.2))

        else:
            test_=a.tail(2)
            train_=a.head(len(a)-2)
        Train.append(train_)
        Test.append(test_)
        
    train_df=pd.concat(Train)
    test_df=pd.concat(Test)
    assert len(train_df[label].unique())==len(test_df[label].unique())
    
    
    train_df.set_index('doc', inplace=True)
    test_df.set_index('doc',inplace=True)
    
    onehot_train = pd.get_dummies(train_df[label])
    onehot_test=pd.get_dummies(test_df[label])
    
    train_target=onehot_train.as_matrix()
    test_target=onehot_test.as_matrix()
    
    aggre=pd.concat([train_df,test_df])
    corpus=pd.concat([aggre['Title'],aggre['Preamble'],aggre['Operative']])
    
    
    tokenizer=Tokenizer(num_words=15000)
    tokenizer.fit_on_texts(corpus)
    
    def pro(x,num):
        bt=tokenizer.texts_to_sequences(x)
        bt_train=pad_sequences(bt,maxlen=num)
        return bt_train
    
    x1_train=pro(train_df.Title,30)
    x2_train=pro(train_df.Preamble,100)
    x3_train=pro(train_df.Operative,100)
    x1_val=pro(test_df.Title,30)
    x2_val=pro(test_df.Preamble,100)
    x3_val=pro(test_df.Operative,100)
    
    
    print("-" * 10)
    print("Training Set")
    print(x1_train.shape)
    print(x2_train.shape)
    print(x3_train.shape)
    print(onehot_train.shape)
   
    print("-" * 10)
    print("Validation Set")
    print(x1_val.shape)
    print(x2_val.shape)
    print(x3_val.shape)
    print(onehot_test.shape)
    
    from keras import Input
    from keras.layers import Embedding,LSTM, concatenate, Dense
    from keras.models import Model
    top_input = Input(
        shape=(30, ), 
        dtype='int32')
    xu_input = Input(
        shape=(100, ), 
        dtype='int32')
    zw_input = Input(
        shape=(100, ), 
        dtype='int32')
    
    embedding_layer=Embedding(15000,256)
    top_embedded=embedding_layer(top_input)
    xu_embedded=embedding_layer(xu_input)
    zw_embedded=embedding_layer(zw_input)
    
    from keras.layers import Bidirectional, GlobalMaxPool1D,Flatten,MaxPooling1D,Dropout
    lstm1=Bidirectional(LSTM(128,dropout=0.15, recurrent_dropout=0.1))
    lstm2=Bidirectional(LSTM(256,dropout=0.15, recurrent_dropout=0.1))
    lstm3=Bidirectional(LSTM(256,dropout=0.15, recurrent_dropout=0.1))
    top_output = lstm1(top_embedded)
    xu_output = lstm2(xu_embedded)
    zw_output = lstm3(zw_embedded)
    
    merged = concatenate(
    [top_output, xu_output,zw_output], 
    axis=-1)
    
    dense1 =Dense(64, activation='relu')(merged)
    drop=Dropout(0.5)(dense1)
    dense2=Dense(18,activation='softmax')

    predictions = dense2(drop)
    
    model = Model(
    inputs=[top_input, xu_input,zw_input], 
    outputs=predictions)
    
    print('Using built in model')
    print(model.summary())
    
    from keras.optimizers import Adam
    lr = 1e-3
    opt = Adam(lr=lr, decay=lr/50)
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy'])


    print('Traing',NUM_EPOCHS,'epochs')

    history = model.fit(

        x=[x1_train, x2_train,x3_train], 
        y=onehot_train,
        batch_size=BATCH_SIZE,
        epochs=NUM_EPOCHS,

        validation_data=(
            [x1_val, x2_val,x3_val], 
            onehot_test
        ),

        shuffle=True
    )
    
    x1_val=pro(df.Title,30)
    x2_val=pro(df.Preamble,100)
    x3_val=pro(df.Operative,100)
    
    re=model.predict([x1_test,x2_test,x3_test])
    y_classes = re.argmax(axis=-1)
    
    dic={}
    for idx,i in enumerate(onehot_train.columns):
        dic[idx]=i
   
    
    classes=[]
    for i in y_classes:
        classes.append(dic[i])
    
    return classes

    
    


# In[32]:


# from pathlib import Path
# from spacy import displacy

# svg = displacy.render(nlp(file), style="ent",minify=True)
# output_path = Path("/sentence.svg")
# output_path.open("w", encoding="utf-8").write(svg)


# In[33]:




# import spacy
# from spacy import displacy
# from pathlib import Path

# nlp = spacy.load('en_core_web_sm', parse=True, tag=True, entity=True)

# sentence_nlp = nlp("John go home to your family")
# svg = displacy.render(sentence_nlp, style="dep")

# output_path = Path("./dependency_plot.svg") # you can keep there only "dependency_plot.svg" if you want to save it in the same folder where you run the script 
# output_path.open("w", encoding="utf-8").write(svg)


# In[34]:


# var displacy = new displaCy('http://localhost:8080', {
#   container: '#displacy',
# })

# function parse(text) {
#   displacy.parse(text)
# }


# js = """ var displacy = new displaCy('http://localhost:8080', {
#   container: '#displacy',
# })

# function parse(text) {
#   displacy.parse(text)
# }
# """
# from IPython.display import display, HTML
# import execjs

# ctx = execjs.compile("""


#     function parse(text,displacy) {
#         var display = new displacy('http://localhost:8080', {
#       container: '#displacy'
#     })

#       display.parse(text)
# } """)
# from spacy import displacy
# ctx.call("parse",file,displacy)


# In[35]:


# def check(df=df):
#     for i in df['Operative']:
#         yield nlp(i)
# print(df['Operative'][1])
# print('--------------------------------------------------')
# print(extract(nlp(df['Operative'][1])))
        
# displacy.render(sents[-5], style='dep', jupyter=True, options={'distance': 70})
# lst=[]
# for i in range(len(df['Operative'])):
#     try:
#         lst.append(extract(nlp(df.loc[i,'Operative'])))
#     except:
#         lst.append('0')


# In[36]:



# childs=[]
# grands=[]
# extragrands=[]
# sons=[]
# daugh=[]
# babies=[]
# sent=sents[-5]
# roots = [token for token in sent if token.head == token]

# for token in sent:
#     if str(token)=='no':
#         roots.append(token)
#     if str(token)=='not':
#         babies.append(token)
# print("roots:",roots)
        
# for root in roots:
#     for item in root.children:
#         if item.dep_!='punct' and item.pos_!='DET' and item.dep_!='aux' and item.dep_!='mark' and item.dep_!='appos':
#             childs.append(item)
#     print("childs:",childs)
    
#     for child in childs:
#         for item in child.children:
#             if item.dep_!='punct'and item.pos_!='DET'and item.dep_!='aux'and item.dep_!='mark':
#                 if str(item)=='comprising':
#                     pass
#                 else:
#                     grands.append(item)
#     print("grands:",grands)
    
#     for grand in grands:
#         for item in grand.children:
#             if item.pos_=='PROPN' or item.pos_=='NOUN'  or item.dep_=='cc' or item.dep_=='ccomp' or item.pos_=='VERB' or item.pos_=='NUM':
#                 if str(item)=='period' or str(item)=='amount' :
#                     grands.remove(grand)
#                 elif item.dep_=='advcl':
#                     pass
#                 elif item.pos_=='VERB' and item in list(grand.lefts):
#                     pass

#                 else:
#                     extragrands.append(item)
                    
#             elif item.pos_=='ADP':
#                 for word in item.children:
#                     if word.dep_=='pobj':   
#                         if sent[word.i-1].pos_=='NUM':
#                             print(666)
#                             daugh.append(sent[word.i-1])
#                             daugh.append(word)
#                         if sent[word.i-1].dep_=='compound' and sent[word.i-2].dep_=='compound':
#                             print(777)
#                             daugh.append(sent[word.i-1])
#                             daugh.append(sent[word.i-2])
#                             daugh.append(word)
#                             extragrands.append(item)
#                         temp=word.nbor().nbor()
# #                         if word.is_ancestor(temp) and temp.pos_=='NUM':
# #                             sons.append(temp)
# #                             sons.append(temp.head)
#                         if word.is_ancestor(temp) and temp.pos_!='DET':
#                             print(888)
#                             print(word,temp)
#                             daugh.append(temp)
#                             if temp in temp.head.lefts:
#                                 daugh.append(temp.head)
#                             else:
#                                 daugh.append(temp.head.head)
#                             for wd in temp.children:
#                                 if wd.dep_=='conj' or wd.dep_=='dobj':
#                                     daugh.append(wd)

#             elif str(item)=='of':
#                 for word in item.children:
#                     if word.pos_=='NOUN':
#                         extragrands.append(item)
#                         sons.append(word)
#                         for wd in word.children:
#                             if wd.dep_=='conj':
#                                 sons.append(wd)
#             elif str(item)=='for':
#                 for word in item.children:
#                     if word.pos_=='NUM':
#                         extragrands.append(item)
#                         sons.append(word)
            
            
#     print("extragrands:",extragrands)
    
#     for extragrand in extragrands:
#         for item in extragrand.children:
#             if item.pos_=='PROPN' or item.pos_=='NOUN' or item.dep_=='nummod' or item.dep_=='pobj' or item.pos_=='NUM':
#                 sons.append(item)
#             if item.pos_=='VERB':
#                 for word in item.children:
#                     if word.pos_=='NOUN':
#                         sons.append(item)
#                         babies.append(word)
#             if item.dep_=='amod':
#                 print(list(extragrand.lefts))
#                 if item in list(extragrand.lefts):
#                     sons.append(item)
#             if str(item)=='of':
#                 for word in item.children:
#                     if word.pos_=='NOUN'and str(word)!='dollars':
#                         sons.append(item)
#                         babies.append(word)
#                         for wd in word.children:
#                             if wd.dep_=='conj':
#                                 babies.append(wd)
#             if str(item)=='on':
#                 for word in item.children:
#                     if word.pos_=='NOUN':
#                         sons.append(item)
#                         babies.append(word)
#                         for wd in word.children:
#                             if wd.dep=='conj' or wd.dep_=='amod' and wd in list(word.lefts):
#                                 babies.append(wd)
                
#     print("sons:",sons)
#     print("daugh:",daugh)
#     print("babies:",babies)

# dic={}
# for t in roots+childs+grands+extragrands+sons+babies+daugh:
#     dic[t]=t.i

# trunk=sorted(dic.items(), key=lambda x: x[1])

# print([t[0] for t in trunk])


# In[37]:


# for token in sents[3]:
#     print(token,'\t',token.pos_,'\t',token.dep_,'\t',token.head)


# In[ ]:




