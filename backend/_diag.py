import time, sys
sys.path.insert(0, ".")
t0 = time.time()
print("START", flush=True)
import app.main
print(f"DONE app.main in {time.time()-t0:.2f}s", flush=True)

