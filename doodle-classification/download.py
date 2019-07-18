import urllib.request

f = open("classes.txt","r")
classes = f.readlines()
f.close()

classes = [c.replace('\n','').replace(' ','_') for c in classes]

def download():
    base_url = 'https://storage.googleapis.com/quickdraw_dataset/full/numpy_bitmap/'
    for c in classes:
        cls_url = c.replace('_', '%20')
        path = base_url + cls_url + '.npy'
        print(path)
        urllib.request.urlretrieve(path, 'data/' + c + '.npy')

download()