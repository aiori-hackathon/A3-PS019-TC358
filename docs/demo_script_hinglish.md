# DataPulse Demo Script (Beginner-friendly Hinglish)

## 1. Introduction
"Hello everyone. Hamara project DataPulse hai, jo AIORI Hackathon 3 ke Cyber Security Track ke PS-019 problem statement par based hai. Iska goal synthetic datasets mein possible personal-data fields identify karna aur check karna hai ki unka purpose aur retention metadata documented hai ya nahi."

## 2. Problem
"Kabhi-kabhi personal data CSV files aur databases mein spread hota hai. Agar humein pata hi nahi ki kaunse fields important hain, ya unka purpose aur retention documented nahi hai, toh review karna difficult ho sakta hai."

## 3. Live demo
"Yeh hamara dashboard hai. Main Run demo scan par click karunga/karungi. Scanner CSV ke column names aur SQLite database ka schema check karta hai. Yeh actual row values ko inventory mein export nahi karta."

"Field inventory mein humein source, field name, data class, purpose aur retention dikhte hain. Jahan purpose ya retention missing hai, wahan Needs review status aata hai."

"Metadata gaps section mein hum missing documentation ko separately dekh sakte hain. Export evidence section se inventory CSV, gaps CSV, scan metrics JSON aur evaluation metrics JSON download kiye ja sakte hain.

"Detection evaluation section mein 43 manually labelled synthetic field names par precision aur recall dikhte hain. Per-class table se pata chalta hai ki har data class par rules kaise perform karte hain. Is sample mein false positives zero hain, lekin do personal-looking fields miss hue: `travel_document_code` aur `house_location`. Isliye high precision ko perfect detection nahi kehna chahiye; test set chhota aur synthetic hai.""

## 4. Technical explanation
"Backend Python mein hai. `scanner.py` detection rules aur metadata checks handle karta hai. Flask dashboard user interface serve karta hai. SQLite local demo database hai, aur synthetic CSV data bhi included hai. 11 automated tests basic scanner behaviour, unusual aliases, known exclusions, metadata gaps, reports aur evaluation checks karte hain."

## 5. Limitations
"Yeh rule-based prototype hai. Field-name matching perfect nahi hoti, isliye result final decision nahi hai. Human review required hai. Is demo mein synthetic data use kiya gaya hai."

## 6. Conclusion
"DataPulse personal-data discovery ko more organised banata hai aur missing purpose/retention evidence highlight karta hai. Thank you."

## Quick run commands
```powershell
python -m pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`, then click **Run demo scan**.


## ML demo addition

“DataPulse mein ab hybrid detection hai. Pehle transparent rules common field names detect karte hain. Agar rule match nahi hota, toh TF-IDF aur Logistic Regression model column name ko classify karta hai. Main ek synthetic CSV upload karunga. Upload hote hi model prediction karta hai. Sirf 90% ya usse zyada confidence wale examples automatic learning pool mein jaate hain. Teen ya usse zyada naye accepted examples hone par model retrain hota hai. Model CSV ke personal data values ko read nahi karta, sirf header names use karta hai. Self-training predictions galat bhi ho sakti hain, isliye confidence aur detection method dashboard par dikhaye jaate hain.”
