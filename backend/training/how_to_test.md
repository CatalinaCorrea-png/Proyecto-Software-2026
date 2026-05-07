
Download the images you want to test the model with.

More specifically, search this: "drone footage people top view" or "aerial view pedestrians"

To test the model, run this on console:

```
 # On one image alone
  python backend/training/test_model.py route/to/image.jpg                                                                                                                                                                           
   
 # On a whole directory       
  python backend/training/test_model.py route/to/carpeta/                                                                                                                                                                           

  # Compare fine-tuned vs base COCO side to side
  python backend/training/test_model.py route/to/image.jpg --compare
```

Results are saved on backend/training/test_output/.


> Deprecated but kept for logs
> 
```
  # Altitude and active model (single v2 model since the dual-model switch was removed)
  curl http://localhost:8000/drone/state

  # Set altitude (kept for telemetry-side testing; no longer changes the model)
  curl -X POST "http://localhost:8000/drone/25"
```