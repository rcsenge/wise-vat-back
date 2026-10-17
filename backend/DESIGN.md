This is a rough idea of the system design, so you understand the idea.

- All of the components should be mocked or hardcoded until our demo works.
- Once the user confirms everything is done for the demo and how much time is left, the determining of what should be prioritized to actually implement can start

System design so far:
- The invoice uploading is the task of the other team, don't worry about it. We first just will use hardcoding
- The invoice uploading will output the json schema already in the repo, we will work with this but if neccessary we can slightly modify it.
- When we receive this json object the first thing to check is to validate the data. Does it have everything to determine whether all required fields have a non null value.
  - If it has a null but required value always send it back with a fail
  - Validate the company's TAX number using the EU VIES to determine if it is a legit company
    - if it is not send it back with a fail
- If it didn't fail by this point: find the transaction that matches the total price of the invoice and map the invoice to the transaction
- then send it to the VAT back rule machine
- The vat back machine:
  - only for these countries (from the transaction): Austria, Germany hard code the VAT back regulation rules (maybe in the sqlite)
  - goes through each item on the invoice finds the country and subcategory rule applying to it
    - if it eligible for the vat back add it to a list of sorts
    - if at least one item on the receipt is eligible add it to the wise account holder (each country collected separately)
- send the total sum per country and the transactions inside to the front end (will be shown later).


      
  