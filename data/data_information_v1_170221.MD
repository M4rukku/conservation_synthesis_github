## Data Usage Instructions for ML Part

In this folder you find three important directories:
    - journal_data
    - positive_samples
    - negative_samples

In Generall Data ending with .pd.json must be read with pandas.read_json, and
.json with json.read().

### Journal Data
First, I will explain the directory that appears a bit out of place:
journal_data. Journal data contains helper data to navigate articles used.
issn_journal_map e.g. maps all issns to their respective journal names.
issn_vol_iss_map, maps all journals to the volumes occurring in our positive data
.
#### Journal Naming
journal_name_to_standard maps some names that might deviate like "The
ecological journal" to a standard identifier "ecological journal". Generally, do
 note that *before working with journals* it is recommended to standardise the
 data. (i.e. unidecode.unidecode(name.strip()).lower())

#### Journal Frequency
It might be useful to consider the distribution of usage for different journals.
 (To select data more specifically.) You can get the distribution using
 journal_usage_frequency.pd.json, which returns the statistics for how our data
 has been obtained (positive samples).

### Positive Samples
A cleaned and complemented (by abstracts) version of the data we got from our
client. Currently you should use v_2_2, where I ensured that journal names are
also standardised.

(data_gathering contains our different ways of getting the data)

### Negative Samples
A set of complementing data. random_journal_metadata contains a pandas (json)
dataframe storing a few hundred thousand random papers in different languages
and from different topics (primarily English though).

cleaned_negative_data_from_comparable_volumes is significantly more complex data
. It is data obtained from the journals and volumes we found in the positive
data. I have removed all obvious positives by their DOI, but the data quality is
 not assured!

 Do also note that the data is a dump of all possible volumes and not cleaned by
  the statistical occurrence of different journals. (If you want to take that
  into model go to Journal Frequency above.)









