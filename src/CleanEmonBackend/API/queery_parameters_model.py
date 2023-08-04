from fastapi import Path, Query

doc_dev_id = \
    Path(title="Device ID",
         description="The dev_id of the device.")
doc_date = \
    Path(title="Date",
         description="A date in YYYY-MM-DD format.")

doc_from_date = \
    Path(title="From Date",
         description="A start date in YYYY-MM-DD format The dev_id of the device. It should be chronologically "
                     "greater or equal to **{from_date}**")

doc_to_date = \
    Path(title="From Date",
         description="A end date in YYYY-MM-DD format The dev_id of the device.")

doc_downsampling = \
    Query(False,
          title="Downsampling",
          description="Specifies whether the returned data should be down sampled.If set to True, the returned data "
                      "will have a larger interval between samples, resulting in a smaller dataset. This can improve "
                      "performance for large datasets.")

doc_sensors = \
    Query(None,
          title="Sensors",
          description="A comma-separated list of sensors to be returned. If present, only sensors defined in that "
                      "list will be returned.")
doc_summarize = \
    Query(title="Summarize",
          description="Specifies the data summarization. If set to true, it returns the sum of all values. If set to "
                      "false, it returns each record for each day.")

doc_simplify = \
    Query(False,
          title="Simplify",
          description="Specifies whether to simplify the response. If set to True, only the pure numerical value will "
                      "be returned.")

doc_field_query = \
    Query(None,
          title="Metadata Field",
          description="Specifies the metadata field to be returned if it exists. If the field does not exist, "
                      "an empty dictionary will be returned. If omitted, all metadata fields will be returned.")
doc_field_path = \
    Path(title="Metadata Field",
         description="Specifies the metadata field to be returned if it exists. If the field does not exist, "
                     "an empty dictionary will be returned. If omitted, all metadata fields will be returned.")

doc_value = Path(title="Metadata Value",
                 description="The metadata value")
