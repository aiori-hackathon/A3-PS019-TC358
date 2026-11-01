# Individual Reflection — DataPulse PS-019

Working on DataPulse helped me understand that privacy work is not only about finding personal information. It is also important to record why the information is needed and how long it should be retained. The project gave me practical experience in Python, CSV files, SQLite, a web dashboard, automated tests, and producing evidence reports.

One challenge was designing detection rules that are simple enough to explain but still useful. A field name such as `email` is easy to recognise, while an unusual field name may be missed. I learned that a rule-based result should be treated as a candidate for human review, not as a final decision.

The project also taught me the value of testing with synthetic data. I added a labelled set with 43 field-name examples and class-wise metrics. The current sample reports precision 1.000 and recall 0.923, with two known misses (`travel_document_code` and `house_location`), which shows why reporting recall and limitations matters instead of claiming perfect detection. Synthetic records allowed me to demonstrate the workflow without exposing real people's information. Automated tests helped check that known field names were detected, unrelated fields were ignored, metadata gaps were reported, and output files were created.

If I continue this project, I would expand the labelled dataset, measure results for each data class, improve explanations for each alert, and add a secure review workflow. Overall, DataPulse improved my understanding of privacy evidence, data discovery, and how to present a technical prototype clearly.

*Personalise this reflection with your actual contribution, challenge, and lesson learned before submitting.*
