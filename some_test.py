from sucuri import Sucuri

sucuri = Sucuri('test/includefile.suc')
sucuri.render()

#for key, value in sucuri.templates.items():
#    print(key, value)