
# Information Extraction for UN Resolutions
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



