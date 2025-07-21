import configparser

def load_db_config(filename='db_config.ini', section='database'):
    parser = configparser.ConfigParser()
    parser.read(filename)

    if parser.has_section(section):
        params = {key: parser.get(section, key) for key in parser.options(section)}
        return params
    else:
        raise Exception(f'Section {section} not found in the {filename} file')