<h1 align='center'>FaceGuard</h1>
<hr>
<h2 align='center'>This project show just tiny part of all opportunities AI and computer vision, so, if you want to see little training project - you are welcome!</h1>

<br>
<p>To run this app you have to install <a href='https://cmake.org/download/' target='_blank'>Cmake</a>.</p> 

Then run: <br>
```python main.py``` 
<br>to run programm.<br><br>

**To add your faces in AI:**<br><br>
**1)** Write pictures to ***data --> faces***<br><br>
**2)** Add code to ***tools --> cv2_functions.py***:<br><br>
*52-62 lines*
```

your_name_image = face_recognition.load_image_file("data/faces/your_name.jpeg"
your_name_face_encoding = face_recognition.face_encodings(your_name_image)[0]

```
<br>
*65-77 lines*<br>

```known_face_encodings = [ ...,
your_name_face_encoding
]

known_face_names = [...,
your_name
]```

