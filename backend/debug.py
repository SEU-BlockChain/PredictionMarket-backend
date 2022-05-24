from lxml import etree

a = """
<p><span data-w-e-type="mention" data-w-e-is-void data-w-e-is-inline data-value="test1" data-info="2">@test1</span></p>
<p><span data-w-e-type="mention" data-w-e-is-void data-w-e-is-inline data-value="test1" data-info="3">@test2</span></p>
"""

tree = etree.HTML(a)

for i in tree.xpath("//span[@data-w-e-type='mention']"):
    uid = i.xpath("@data-info")[0]
    username = i.xpath("text()")[0].replace("@", "")
    print(username)
    i.set("style", "color: rgb(54, 88, 226);")
    i.set("uid", uid)

print(etree.tostring(tree).decode("utf-8")[12:-14])
