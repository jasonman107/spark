#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
A collections of builtin avro functions
"""


from pyspark import since, SparkContext
from pyspark.rdd import ignore_unicode_prefix
from pyspark.sql.column import Column, _to_java_column
from pyspark.util import _print_missing_jar


@ignore_unicode_prefix
@since(3.0)
def from_avro(data, jsonFormatSchema, options={}):
    """
    Converts a binary column of avro format into its corresponding catalyst value. The specified
    schema must match the read data, otherwise the behavior is undefined: it may fail or return
    arbitrary result.

    Note: Avro is built-in but external data source module since Spark 2.4. Please deploy the
    application as per the deployment section of "Apache Avro Data Source Guide".

    :param data: the binary column.
    :param jsonFormatSchema: the avro schema in JSON string format.
    :param options: options to control how the Avro record is parsed.

    >>> from pyspark.sql import Row
    >>> from pyspark.sql.avro.functions import from_avro, to_avro
    >>> data = [(1, Row(name='Alice', age=2))]
    >>> df = spark.createDataFrame(data, ("key", "value"))
    >>> avroDf = df.select(to_avro(df.value).alias("avro"))
    >>> avroDf.collect()
    [Row(avro=bytearray(b'\\x00\\x00\\x04\\x00\\nAlice'))]
    >>> jsonFormatSchema = '''{"type":"record","name":"topLevelRecord","fields":
    ...     [{"name":"avro","type":[{"type":"record","name":"value","namespace":"topLevelRecord",
    ...     "fields":[{"name":"age","type":["long","null"]},
    ...     {"name":"name","type":["string","null"]}]},"null"]}]}'''
    >>> avroDf.select(from_avro(avroDf.avro, jsonFormatSchema).alias("value")).collect()
    [Row(value=Row(avro=Row(age=2, name=u'Alice')))]
    """

    sc = SparkContext._active_spark_context
    try:
        jc = sc._jvm.org.apache.spark.sql.avro.functions.from_avro(
            _to_java_column(data), jsonFormatSchema, options)
    except TypeError as e:
        if str(e) == "'JavaPackage' object is not callable":
            _print_missing_jar("Avro", "avro", "avro", sc.version)
        raise
    return Column(jc)


@ignore_unicode_prefix
@since(3.0)
def to_avro(data):
    """
    Converts a column into binary of avro format.

    Note: Avro is built-in but external data source module since Spark 2.4. Please deploy the
    application as per the deployment section of "Apache Avro Data Source Guide".

    :param data: the data column.

    >>> from pyspark.sql import Row
    >>> from pyspark.sql.avro.functions import to_avro
    >>> data = [(1, Row(name='Alice', age=2))]
    >>> df = spark.createDataFrame(data, ("key", "value"))
    >>> df.select(to_avro(df.value).alias("avro")).collect()
    [Row(avro=bytearray(b'\\x00\\x00\\x04\\x00\\nAlice'))]
    """

    sc = SparkContext._active_spark_context
    try:
        jc = sc._jvm.org.apache.spark.sql.avro.functions.to_avro(_to_java_column(data))
    except TypeError as e:
        if str(e) == "'JavaPackage' object is not callable":
            _print_missing_jar("Avro", "avro", "avro", sc.version)
        raise
    return Column(jc)


def _test():
    import os
    import sys
    from pyspark.testing.utils import search_jar
    avro_jar = search_jar("external/avro", "spark-avro")
    if avro_jar is None:
        print(
            "Skipping all Avro Python tests as the optional Avro project was "
            "not compiled into a JAR. To run these tests, "
            "you need to build Spark with 'build/sbt -Pavro package' or "
            "'build/mvn -Pavro package' before running this test.")
        sys.exit(0)
    else:
        existing_args = os.environ.get("PYSPARK_SUBMIT_ARGS", "pyspark-shell")
        jars_args = "--jars %s" % avro_jar
        os.environ["PYSPARK_SUBMIT_ARGS"] = " ".join([jars_args, existing_args])

    import doctest
    from pyspark.sql import Row, SparkSession
    import pyspark.sql.avro.functions
    globs = pyspark.sql.avro.functions.__dict__.copy()
    spark = SparkSession.builder\
        .master("local[4]")\
        .appName("sql.avro.functions tests")\
        .getOrCreate()
    globs['spark'] = spark
    (failure_count, test_count) = doctest.testmod(
        pyspark.sql.avro.functions, globs=globs,
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    spark.stop()
    if failure_count:
        sys.exit(-1)


if __name__ == "__main__":
    _test()
