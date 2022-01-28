import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import requests


st.set_page_config(page_title="Collections Assessment Data Exploration App",
                   layout="wide"
                   )
sample_file = "https://raw.githubusercontent.com/adgray987/collections-assessment-eda/main/data_raw/assessment_list_report.csv"
intro_url = "https://raw.githubusercontent.com/adgray987/collections-assessment-app/main/intro_text.txt"
conclusion_url = "https://raw.githubusercontent.com/adgray987/collections-assessment-app/main/conclusion_text.txt"

#---Title and intro text
##def get_text(url):
##    response = requests.get(url)
##    content = response.text
##    content_string = f"{content}"
##    return(content_string)

st.title("Assessment Snapshot")
st.subheader("Assessment Snapshot is a tool for exploring collections assessment data exported from ArchivesSpace.")
##
##intro = get_text(intro_url)
##st.markdown(intro)
##conclusion = get_text(conclusion_url)
##st.markdown(conclusion)

#---Get data
data = pd.read_csv(sample_file, header=3)

# Load CSV with st.file_uploader()
# Upload file option
##uploaded_file = st.file_uploader(label="Upload an Assessment Record List Report (CSV) from ArchivesSpace.",
##                                 help="Upload an Assessment Record List Report (CSV) from ArchivesSpace. The column headers have to be in row 3 or the data may not load properly. Large files may take longer to process.")
##if uploaded_file is not None:
##    data = pd.read_csv(uploaded_file, header=2)
##else: # sample data for public version
##    data = pd.read_csv(sample_file, header=3)

#@st.cache
def load_data(csv):
    assessment = csv.copy()
    assessment.dropna(how="all", inplace=True, axis=1)
    new_names = lambda x: x.replace("_"," ").title()
    assessment.rename(columns=new_names, inplace=True)
# Trim and collapse whitespace for ALL columns of dtype 'object' (i.e. strings)
    text_cols = list(assessment.select_dtypes(include='object').columns)
    assessment[text_cols] = assessment.select_dtypes(include='object').apply(lambda x: x.str.replace(r'\s+',' ').str.strip())
    assessment["Purpose"] = assessment["Purpose"].str.title()
    return assessment

def make_slider(name):
    min_rating = int(df[name].min())
    max_rating = int(df[name].max())
    option = st.sidebar.slider(f"{name}",
                                  min_rating, max_rating, (min_rating, max_rating))
    return option

def make_size_slider(name, tip):
    min_rating = int(df[name].min())
    max_rating = int(df[name].max())
    option = st.sidebar.slider(f"{name}",
                                  min_rating, max_rating, (min_rating, max_rating),
                               help=tip)
    return option

#@st.cache
def get_values(tup):
    values = [i for i in range(tup[0], tup[1]+1)]
    return values

df = load_data(data)




# Create list of column names for filterable variables
ratings_names = list(df.columns[(df.columns.str.endswith('Rating') == True)])
ratings_names.sort()
purposes = list(df["Purpose"].unique())


# Create list of bool-type cols
bool_cols = []
for col in df.columns:
    if df[col].isin(["Yes", "No", np.nan]).all(skipna=False):
        bool_cols.append(col)


df.dropna(how="any", inplace=True, subset=ratings_names)
df[ratings_names] = df[ratings_names].astype("int64")
# Parse numbers from strings in extent field if units are known and consitent. Otherwise comment out line below.
##df["Surveyed Extent (cubic feet)"] = df["Surveyed Extent"].str.extract(r"([\d\.]+)")[0].astype("float").round().replace(0, 1).astype("int")
# Say units are cubic feet for example
df["Surveyed Extent (cubic feet)"] = df["Surveyed Extent"].astype("float").round().replace(0, 1).astype("int")

base_cols =  ["Linked Records Record Title", "Surveyed Extent (cubic feet)", "Surveyed Extent", "Scope", "Sensitive Material"] + ratings_names



# Sidebar filters
st.sidebar.subheader("Assessment Purpose")
purpose_selectbox = st.sidebar.selectbox(label="Select one", options=["All"] + purposes, index=0)

#---size_slider break when results == 0 because subset tries converting NaN to integer.---

#st.sidebar.subheader("Size")
#size_slider = make_size_slider("Surveyed Extent (cubic feet)", "Collections smaller than 1 cubic foot are rounded up to 1.")

#---

st.sidebar.subheader("Ratings")

slider_dict = {}
for name in ratings_names:
    slider_dict.update({name : make_slider(name)})


#---changes below reflect removal of size filter---

for rowi, row, in df[ratings_names].iterrows():
    matches = []
    for key in slider_dict:
        for i in slider_dict[key]:
            match = False
            if df.loc[rowi,key] in [i for i in range(slider_dict[key][0], slider_dict[key][1]+1)]:
                match = True
            matches.append(match)
            df.at[rowi,"match"] = matches
            df.at[rowi,"match2"] = all(matches)

if purpose_selectbox == "All":
    subset = df[(df["match2"] == True)]
##                & (df["Surveyed Extent (cubic feet)"].isin([i for i in range(size_slider[0], size_slider[1]+1)]))]

else:
    subset = df[(df["match2"] == True)
##                & (df["Surveyed Extent (cubic feet)"].isin([i for i in range(size_slider[0], size_slider[1]+1)]))
                & (df["Purpose"] == purpose_selectbox)]

total_rows = len(subset)
#---

#---Data for extents chart
## Breaks with long dfs
sub_e_min = int(subset["Surveyed Extent (cubic feet)"].min())
sub_e_max = int(subset["Surveyed Extent (cubic feet)"].max())
total_e = subset["Surveyed Extent (cubic feet)"].sum()
notes = df.filter(regex="Notes?$", axis=1).columns.to_list()

#---Results summary
st.header("Collections Assessment Overview")
st.write(f"{total_rows} records found.\n\n")

#---Ratings counts heatmap
st.subheader("Collection Ratings")
# Data for Ratings heatmap-style table
ratings_counts = pd.DataFrame(subset[ratings_names[0]].value_counts(sort=False))
for name in ratings_names[1:-1]:
    ratings_counts[name] = subset[name].value_counts(sort=False)

print("Ratings counts:")
print(ratings_counts)

# Ratings heatmap-style table
data = [(1,2,3,4,5,6)]
ratings_counts = pd.DataFrame(data,columns=ratings_names[:-1])
for name in ratings_names[:-1]:
    ratings_counts[name] = subset[name].value_counts(sort=False)
    
r1, r2, r3, r4, r5, r6 = [subset[ratings_names[0]].value_counts(sort=False), 
                          subset[ratings_names[1]].value_counts(sort=False),
                          subset[ratings_names[2]].value_counts(sort=False),
                          subset[ratings_names[3]].value_counts(sort=False), 
                          subset[ratings_names[4]].value_counts(sort=False),
                          subset[ratings_names[5]].value_counts(sort=False)]

ratings_counts = pd.DataFrame({ratings_names[0] : r1, 
                                ratings_names[1] : r2,
                                ratings_names[2] : r3, 
                                ratings_names[4] : r4,
                                ratings_names[5] : r5, 
                                ratings_names[6] : r6}, index=[1,2,3,4,5])

ratings_counts_transposed = ratings_counts.T.reset_index(drop=False)
new_ratings_names = {1: '1: very poor', 2: '2: poor', 3: '3: good', 4: '4: very good', 5: '5: excellent'}
ratings_counts_transposed.rename(columns=new_ratings_names, inplace=True)

melted = ratings_counts_transposed.melt(id_vars=["index"], var_name="Rating", value_name="Count"
                                        ).astype({"Rating":"string"}, copy=False).rename(columns={"Count":"Number of Collections"})
melted["index"] = melted["index"].str.replace(" Rating","")


# Ratings hearmap-style chart
heatmap1 = alt.Chart(melted).mark_rect().encode(
    x=alt.X("Rating:O", title=None),
    y=alt.Y("index:O", title=None),
    color=alt.Color("Number of Collections:Q", legend=alt.Legend(direction="horizontal", orient="top")),
    tooltip="Number of Collections",
    ).properties(
        width="container",
        height=450,
        ).configure_axis(
            labelFontSize=14,
            labelAngle=0
            )

st.altair_chart(heatmap1, use_container_width=True)

#---Extents summary
# Make Altair chart for extents
st.subheader("Collection Sizes (surveyed extent)")
st.write(f"Surveyed extents in this selection range from approximately {sub_e_min} to {sub_e_max} cubic feet.\n\n")
st.write(f"Total combined footage is approximately {total_e} cubic feet.\n\n")
extents_hist = alt.Chart(subset).mark_bar().encode(
    alt.X("Surveyed Extent (cubic feet):Q", bin=True),
    y="count()"
    ).properties(title="Distribution of Survey Size")

summary = subset["Surveyed Extent (cubic feet)"].rename("Surveyed Extent").describe()

statcol1, statcol2 = st.columns([2, 1])
with statcol1:
    st.altair_chart(extents_hist, use_container_width=True)
with statcol2:
    st.write(summary)

#---Large collections
# Removed this

#---Documentation, Special formats, etc.
st.subheader("Documentation, Special Formats, and Preservation Concerns")
# Counting bool-type cols
bool_counts = subset[bool_cols].apply(lambda x: x.value_counts())
bool_display = bool_counts.T["Yes"].dropna().rename("# of Collections")

# Bool-type chart
bool_chart_data = bool_display.reset_index().rename(columns={"index":"Document/Format Type"})
bool_chart = alt.Chart(bool_chart_data).mark_bar().encode(
    x="# of Collections",
    y="Document/Format Type",
    tooltip=["Document/Format Type", "# of Collections"]
)
st.altair_chart(bool_chart, use_container_width=True)

#---Results table
st.write(f"{total_rows} records found.\n\n")
column_picker = st.multiselect('Add or remove columns here.',
                              df.columns.tolist(),default=base_cols)
instructions, download = st.columns(2)
with instructions:
    st.write("Sort results by clicking on a column header.")
with download:
# download button
    csv_data = subset[column_picker].to_csv(index=False)
    st.download_button(
        label="Download CSV", data=csv_data,
        file_name="assessment_eda_example.csv", mime="text/csv")
    
st.write(subset[column_picker])
