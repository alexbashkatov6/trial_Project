import pandas as pd
import os

folder = os.path.join(os.getcwd(), "station_out_config")
file = os.path.join(folder, "result.xlsx")

d = {"a": [], "b": []}
df = pd.DataFrame(data=d)
# df.to_excel(file, index=False)
