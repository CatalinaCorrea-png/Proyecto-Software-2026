
Download the images you want to test the model with.

More specifically, search this: "drone footage people top view" or "aerial view pedestrians"

To test the model, run this on console:

```
 # On one image alone
  python backend/training/test_model.py ruta/a/imagen.jpg                                                                                                                                                                           
   
 # On a whole directory       
  python backend/training/test_model.py ruta/a/carpeta/                                                                                                                                                                           

  # Compare fine-tuned vs base COCO side to side
  python backend/training/test_model.py ruta/a/imagen.jpg --compare
```

Results are saved on backend/training/test_output/.

```
  # Altitude and active model
  curl http://localhost:8000/drone/state 
  
  # Switch to low altitude -> base
  curl -X POST "http://localhost:8000/drone/5"

  # Switch to high altitude -> fine tuned
  curl -X POST "http://localhost:8000/drone/25"
```