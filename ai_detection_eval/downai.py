import gptzzzs

thing = gptzzzs.Gptzzzs()

text = "Australia's arts funding reforms over the past decade have significantly reshaped the nation's cultural landscape. These changes have profoundly influenced how the local arts organisations operate, fund their projects, and engage with audiences locally and internationally. While many reforms aimed at expanding diversity, international collaboration, and institutional stability have proven beneficial, they have clearly exposed deeper tensions  within the sector. The increased reliance on diversified funding sources—particularly private sponsorship and international partnerships which has undeniably strengthened the global presence and creative scope of major events such as the Biennale of Sydney. However, this funding approach also raises critical questions about the independence of artistic decisions and the sustainability of smaller, community-based or experimental initiatives. Without careful management, Australia's arts ecology risks becoming overly centralised and commercially driven, reducing space for genuine innovation and grassroots creativity." # Put your text here

response = thing.basic_change_text(text)
print(response)