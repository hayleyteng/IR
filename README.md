
Information Extraction for UN Resolutions
===================================
  In current system, only the pdf or word documents are stored in the system.<br />
  It is hard for managers to query keywords or file in terms of categories. <br />
  This project aims to solve this problem for the UN resolution system.


## 1. Metadata with Regular Expression

  Since all of the metadata has some specific pattern, RE would be efficient to locate these basic information<br />
  This task consists of two parts: fields extraction and basic segementation.<br />

### 1.1 Metadata for documents
> The sample extracted metadata fields are shown below.<br />
> Title and Closing Formula, which are not necessaily metadata, are also included. <br />

   * Doc Name：N1846596
   <br/>Note*：Doc Name does not need extraction. It is set as index.
   * ID：A/RES/73/277
   * Session: Seventy-third Session
   * Agenda Items：148
   * Proponent Authority：The Fifth Committee
   * Approval Date: 2018-12-22
   * Title
       * Financing of the International Residual Mechanism for Criminal Tribunals
   * Closing Formula
       * 65th plenary meeting
       * 22 December 2018 <br />

The result is shown as follows:<br />

![images](https://github.com/hayleyteng/UN/blob/master/01.png "01")

### 1.2 Paragraph Segmentation
> We extract   `operative, preamble, annex and footnote information`, which would be crucial to content analysis and future extraction.<br />
> The figure below shows one example with    `'fn'` = footnote:

![2-images](https://github.com/hayleyteng/UN/blob/master/02.png "02")


## 2. Task-based information extraction

  This part consists of document abbreviation, deadlines extraction, references extraction and database filtering.<br />
  These tasks are based on the first part, and are required with higher precision. <br />

### 2.1 Document abbreviation
> The abbreviation is only done for   `operative paragraphs`.<br />
> The sample output is shown as follows. Words in red belong to   `wrong abbreviations`.<br />
> The testing accuracy for this task is  `0.88`.<br />

![3-images](https://github.com/hayleyteng/UN/blob/master/03.png "03")

### 2.2 Refences and deadlines
> Here our goal is to find out past resolutions and future dates.<br />
> We can make more precise matches thanks to their    `specific formats`.<br />
> Sample outputs are shown as follows:<br />

#### Refences:
      >>>b.refence(file)
      ['resolutions 1980/67 1989/84',
      'resolution 69/313',
      'resolutions 53/199 61/185',
      'decision XIII/5',
      'decision 14/30',
      'decision XII/19',
      'resolution 70/1',
      'decision 14/5']

#### Referred resolutions:
      >>>b.refered_doc(file,df)
      ['N1523222', 'N0650553', 'N1529189']

#### Future Date and Year:
      >>>b.future_date(file)
      (['8 June 2020', '11 June 2020'], ['2030', '2020', '2019'])
      ###  Note that there are two lists returned
      ###  Year list is used when only year or year range is mentioned
