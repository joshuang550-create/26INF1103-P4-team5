**Project Initial Details (Lab P4-Team 5\)**

**Problem Statement and Target Users**

What ***real-world problem*** does your application aim to solve?

In today’s world where food is heavily modified to cater to a variety of different preferences, its ingredients likewise are also becoming harder to track even with its full technical term being listed. Additionally most companies bury their ingredient lists with nutritional labels that don’t help to interpret the health risks or benefits effectively, especially to people who may not be nutritionally literate. Therefore, for individuals managing diabetes, hypertension, or hereditary conditions, the time taken to manually reference the ingredients against their own risk factors will be extremely time-consuming and will likely include human errors from fatigue over time. Furthermore, the existing market solutions only provide general-wellness scores or nutritional-based facts. 

In summary, our application aims to help individuals managing existing or hereditary health conditions accurately track the health risks of the ingredients found in the products that they consume. By cross-referencing health profiles to the ingredients of a product, the application identifies its severity and risks then summarises it as a complete recommendation to its user.

Who are the ***intended users*** of the application?

- Individuals managing chronic conditions, food allergies or intolerance that need to monitor their nutritional intake. 

- **Caregivers** can also utilise this application to manage food choices on behalf of someone (e.g. handicapped, elderly)

**User Inputs**

What information or data will ***users provide*** to the system?

Health Profile:

- **Age**  
- **Gender**  
- **Height/Weight/BMI**  
- **Existing** **Health and Hereditary conditions**.

Product Information: 

- **Brand and name of Product**  
- **Nutritional Label/Ingredients**

**Use of AI**

How will ***AI be utilized*** within the application?

AI will look at user input \> check OpenFoodFacts database (if list of ingredients is not provided by user) \> confirm product selection with user.

AI will then base a defined reference framework (either built-in or outsource) and reason with ingredient text \- matching scientific chemical synonyms, interpret nutritional value against the thresholds of the referenced framework, and identify any allergen conflicts \- and produce a risk assessment with justification.

What outputs, insights, or recommendations will the ***AI generate*** from the user inputs?

AI will output:

1. Overall **risk verdict** of product (**Low, Med, High**)  
2. **Flagged ingredients with reasoning**  
3. **Allergen** conflicts  
4. **Brief explanation** on whether this **food product is or isn’t a concern** for the user.

**Business Rules**

What ***business rules, validations, or decision-making logic*** will be applied to the AI-generated outputs?

- Classification of severity and its respective outputs to the user:  
  If flagged as “high”  
  * system verdict is “to avoid”  
  * Elif “medium”  
    * system verdict is “caution”  
  * Else  
    * system verdict is “okay”

      

      

- If allergen is detected \> ignore severity \> automatically output “avoid”

- Reject if database lacks product’s ingredient and nutritional list 

## **GitHub Repository URL**

[https://github.com/joshuang550-create/26-INF1103-P4-team5.git](https://github.com/joshuang550-create/26-INF1103-P4-team5.git)   
