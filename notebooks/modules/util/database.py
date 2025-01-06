# standard modules
import json
import pandas as pd

# sqlalchemy imports
from sqlalchemy import create_engine, Column, Integer, String, select, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.sql import text, case, literal_column

# custom modules
from modules.util.config import get_config_by_id
from modules.util.helpers import Logger

Base = declarative_base()
ViewBase = declarative_base(name="ViewBase")


class SQLAlchemyClient:

    """
    Database Manager to handle all operations related to the database
    Raises:
        EnvironmentError: If any variable is missing or if the values of certain necessary variables are blank.
    """

    def __init__(self, config_id: str):

        """
        Initializes the database connection using the provided configuration ID.
        Args:
            config_id (str): The identifier for the database configuration.
        Raises:
            ValueError: If the configuration for the given config_id is not found.
        Attributes:
            config (dict): The configuration dictionary loaded using the config_id.
            tenantid (str): The tenant identifier, same as config_id.
            __database_url (str): The database connection URL.
            __sqlalchemy_echo (bool): Flag to enable or disable SQLAlchemy echo.
            engine (Engine): The SQLAlchemy engine instance.
            Session (sessionmaker): The sessionmaker bound to the engine.
            drop_reload (bool): Flag indicating whether to drop and reload the database.
        """

        self.config = get_config_by_id(config_id)
        if self.config is None:
            raise ValueError(f"{config_id} configuration not loaded (or) not found")

        self.log = Logger.get_logger(config_id)

        self.tenantid = config_id
        self.__database_url = self.config["database"]["connection"]
        self.__sqlalchemy_echo = self.config["database"].get("sqlalchemy_echo", False)
        self.engine = create_engine(self.__database_url, echo=self.__sqlalchemy_echo)
        self.drop_reload = self.config["database"]["drop_reload"]
        self.views = [
            model
            for model in ViewBase.__subclasses__()
            if hasattr(model, "__tablename__")
        ]
        # ---- Logging ---- #
        self.log.info(f"[DB] Tenant ID: {self.tenantid}")
        self.log.info(f"[DB] Database Connection: {self.__database_url}")
        self.log.debug(f"[DB] SQLAlchemy Echo: {self.__sqlalchemy_echo}")
        self.log.info(f"[DB] Drop Reload: {self.drop_reload}")

        self.Session = sessionmaker(bind=self.engine)

    def get_database_url(self) -> str:

        """
        Retrieves the database URL as a string.
        Returns:
            str: The database URL.
        """

        return str(self.__database_url)

    def table_create_all(self) -> None:

        """
        Creates all tables and views defined in the SQLAlchemy metadata.
        This method uses the SQLAlchemy `create_all` function to create all tables
        defined in the `Base` metadata.
        Returns:
            None
        """

        Base.metadata.create_all(self.engine)
        tables = Base.metadata.tables.keys()

        for table in tables:
            self.log.debug(f"[DB] Table Created: {table}")

        for view in self.views:
            SQLAlchemyClient.create_or_replace_view(self.engine, view)
            self.log.debug(f"[DB] View Created: {view.__tablename__}")

    def table_drop_all(self) -> None:

        """
        Drops all tables and views from the database.
        This method drops all tables defined in the SQLAlchemy Base metadata
        and then drops all views listed in the `self.views` attribute.
        Returns:
            None
        """

        Base.metadata.drop_all(self.engine)
        for view in self.views:
            SQLAlchemyClient.drop_view(self.engine, view)

    def truncate(self, model) -> None:

        """
        Truncate all rows in the specified model table for the current tenant.
        Args:
            model: The SQLAlchemy model class representing the table to truncate.
        Returns:
            None
        Steps:
            Deletes all rows in the specified model table for the current tenant.
            Logs the number of rows deleted.
            Commits the transaction to the database.
        Raises:
            SQLAlchemyError: If an error occurs during the database operation.
        """

        with self.Session() as session:
            query = session.query(model).filter(model.tenantid == self.tenantid)
            rows = query.delete(synchronize_session=False)
            self.log.warning(f"[DB] TRUNCATE {model.__tablename__}: {rows}")
            session.commit()

    def insert_batches(self, data) -> None:

        """
        Insert a batch of data objects into the database.
        This method takes a list of data objects, sets their tenant ID to the
        current instance's tenant ID, and inserts them into the database in bulk.
        Args:
            data (list): A list of data objects to be inserted. Each object must
                         have a `__tablename__` attribute and a `tenantid` attribute.
        Returns:
            None
        Logs:
            Logs the table name and the number of objects being inserted.
        """

        self.log.info(f"[DB] INSERT {data[0].__tablename__}: {len(data)}")
        for obj in data:
            obj.tenantid = self.tenantid
        with self.Session() as session:
            session.bulk_save_objects(data)
            session.commit()

    def count(self, model) -> str:

        """
        Count the number of records in the database for a given model.
        Args:
            model: The SQLAlchemy model class for which the count of records is to be retrieved.
        Returns:
            str: The count of records as a string.
        """

        with self.Session() as session:
            return str(session.query(model).count())

    def __to_dict(self, obj) -> dict:

        """
        Convert a SQLAlchemy ORM object to a dictionary.
        Args:
            obj: The SQLAlchemy ORM object to be converted.
        Returns:
            dict: A dictionary representation of the ORM object, where the keys are column names and the values are the corresponding attribute values of the object.
        """

        return {
            column.name: getattr(obj, column.name) for column in obj.__table__.columns
        }

    def select(
        self,
        model,
        fields: list = [],
        distinct: bool = False,
        where=None,
        orderby: list = [],
    ) -> dict:

        """
        Select records from the model class (table)

        Args:
            model : A SQLAlchemy model class
            fields(list, optional): List of field names to be selected. If no value is provided, all fields are selected
            distinct(bool, optional): Whether to return distinct values or not. Defaults to False.
            where(list, optional): List of where conditions
            orderby(list, optional): List of fields sorted in ascending order
        Returns:
            dict: A dictionary with the list of values and headers of the table. Can be used to load into a pandas dataframe.
        """

        with self.Session() as session:
            results = []
            query = session.query(model)
            query = query.filter(model.tenantid == self.tenantid)

            if fields:
                query = query.with_entities(
                    *(getattr(model, field) for field in fields)
                )

            if where is not None:
                query = query.filter(*where)

            if orderby:
                query = query.order_by(*(getattr(model, field) for field in orderby))

            if distinct == True:
                query = query.distinct()

            self.log.debug(query.statement)
            data = query.all()

            if fields:
                results = [dict(zip(fields, row)) for row in data]
            else:
                results = [self.__to_dict(row) for row in data]

            self.log.info(f"[DB] SELECT {model.__tablename__}: {len(results)}")
            return results

    @staticmethod
    def convert_lists_to_strings(row):

        """
        Defines a static method to convert lists to strings
        """

        for key, value in row.items():
            if isinstance(value, list):
                if not value:
                    row[key] = None
                else:
                    row[key] = json.dumps(value)
        return row

    @staticmethod
    def dataframe_to_object(df: pd.DataFrame, model) -> list:

        """
        Converts a pandas DataFrame into a list of model instances.
        Args:
            df (pd.DataFrame): The DataFrame containing the data to be converted.
            model (Type): The model class to instantiate with the DataFrame rows.
        Returns:
            list: A list of model instances created from the DataFrame rows.
        """

        instances = []
        for _, row in df.iterrows():
            row_data = row.to_dict()
            instance = model(**row_data)
            instances.append(instance)
        return instances

    @staticmethod
    def create_or_replace_view(engine, model):

        """
        Create or replace a SQL view based on the provided SQLAlchemy model.
        This function generates a SQL statement to create or replace a view using the
        definition provided in the SQLAlchemy model. It supports SQLite, PostgreSQL,
        and SAP HANA databases. For other databases, it defaults to creating a view.
        Args:
            engine (sqlalchemy.engine.Engine): The SQLAlchemy engine connected to the database.
            model (sqlalchemy.ext.declarative.api.DeclarativeMeta): The SQLAlchemy model containing
                the table definition and view name.
        Raises:
            sqlalchemy.exc.SQLAlchemyError: If there is an error executing the SQL statement.
        Example:
            class MyModel(Base):
                __tablename__ = 'my_view'
                __definition__ = select([table1.c.column1, table2.c.column2]).select_from(
                    table1.join(table2, table1.c.id == table2.c.id)
            engine = create_engine('sqlite:///mydatabase.db')
            create_or_replace_view(engine, MyModel)
        """

        view_name = model.__tablename__

        sql_statement = model.__definition__.compile(
            engine, compile_kwargs={"literal_binds": True}
        ).string

        with engine.connect() as connection:
            if engine.dialect.name == "sqlite":
                connection.execute(text(f"DROP VIEW IF EXISTS {view_name}"))
                connection.execute(
                    text(f"CREATE VIEW IF NOT EXISTS {view_name} AS {sql_statement}")
                )
            elif engine.dialect.name == "postgresql":
                connection.execute(
                    text(f'CREATE OR REPLACE VIEW "{view_name}" AS {sql_statement}')
                )
                connection.commit()
            elif engine.dialect.name == "hana":
                connection.execute(
                    text(f"CREATE OR REPLACE VIEW {view_name} AS {sql_statement}")
                )
            else:
                connection.execute(text(f"CREATE VIEW {view_name} AS {sql_statement}"))

    @staticmethod
    def drop_view(engine, model):

        """
        Drops a database view if it exists.
        Parameters:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine connected to the database.
        model (sqlalchemy.ext.declarative.api.DeclarativeMeta): The SQLAlchemy model representing the view to be dropped.
        The function checks the dialect of the database engine and executes the appropriate SQL command to drop the view.
        - For SQLite and PostgreSQL, it uses "DROP VIEW IF EXISTS".
        - For HANA, it uses "DROP VIEW".
        - For other databases, it defaults to "DROP VIEW".
        Note:
        - Ensure that the model has a `__tablename__` attribute that specifies the name of the view.
        """

        with engine.connect() as connection:
            if engine.dialect.name == "sqlite":
                connection.execute(text(f"DROP VIEW IF EXISTS {model.__tablename__}"))
            elif engine.dialect.name == "postgresql":
                connection.execute(text(f"DROP VIEW IF EXISTS {model.__tablename__}"))
            elif engine.dialect.name == "hana":
                connection.execute(text(f"DROP VIEW {model.__tablename__}"))
            else:
                connection.execute(text(f"DROP VIEW {model.__tablename__}"))


# ---------------------------------------------------------------------------------------------------------------------------- #
# Models: Tables
# ---------------------------------------------------------------------------------------------------------------------------- #


class ExternalData_EQU(Base):
    __tablename__ = "T_PAI_EXTERNALDATA"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    systemId = Column(String)  # Using String for object type
    externalId = Column(String)
    objectType = Column(String)
    ainObjectId = Column(String)
    systemType = Column(String)
    systemName = Column(String)
    externalObjectTypeCode = Column(String)
    externalIdUrl = Column(String)  # Assuming externalIdUrl should remain as Float


class ExternalData_FLOC(Base):
    __tablename__ = "T_PAI_EXTERNALDATA_FLOC"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    systemId = Column(String)  # Using String for object type
    externalId = Column(String)
    objectType = Column(String)
    ainObjectId = Column(String)
    systemType = Column(String)
    systemName = Column(String)
    externalObjectTypeCode = Column(String)
    externalIdUrl = Column(String)  # Assuming externalIdUrl should remain as Float


class APM_IndicatorPositions(Base):
    __tablename__ = "T_APM_INDICATOR_POSITIONS"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    ID = Column(String)
    SSID = Column(String)
    name = Column(String)


class EquipmentHeader(Base):
    __tablename__ = "T_PAI_EQU_HEADER"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    equipmentId = Column(String)
    name = Column(String)
    internalId = Column(String)
    status = Column(String)
    statusDescription = Column(String)
    version = Column(String)
    hasInRevision = Column(String)
    modelId = Column(String)
    modelName = Column(String)
    shortDescription = Column(String)
    templateId = Column(String)
    subclass = Column(String)
    modelTemplate = Column(String)
    location = Column(String)
    criticalityCode = Column(String)
    criticalityDescription = Column(String)
    manufacturer = Column(String)
    completeness = Column(String)
    createdOn = Column(String)
    changedOn = Column(String)
    publishedOn = Column(String)
    serialNumber = Column(String)
    batchNumber = Column(String)
    tagNumber = Column(String)
    lifeCycle = Column(String)
    lifeCycleDescription = Column(String)
    source = Column(String)
    imageURL = Column(String)
    operator = Column(String)
    coordinates = Column(String)
    installationDate = Column(String)
    equipmentStatus = Column(String)
    buildDate = Column(String)
    isOperatorValid = Column(String)
    modelVersion = Column(String)
    soldTo = Column(String)
    image = Column(String)
    consume = Column(String)
    dealer = Column(String)
    serviceProvider = Column(String)
    primaryExternalId = Column(String)
    equipmentSearchTerms = Column(String)
    sourceSearchTerms = Column(String)
    manufacturerSearchTerms = Column(String)
    operatorSearchTerms = Column(String)
    class_ = Column(String)


class FlocHeader(Base):
    __tablename__ = "T_PAI_FLOC_HEADER"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    id = Column(String)
    name = Column(String)
    internalId = Column(String)
    status = Column(String)
    statusDescription = Column(String)
    version = Column(String)
    hasInRevision = Column(String)
    modelId = Column(String)
    modelName = Column(String)
    shortDescription = Column(String)
    templateId = Column(String)
    subclass = Column(String)
    modelTemplate = Column(String)
    location = Column(String)
    criticalityCode = Column(String)
    criticalityDescription = Column(String)
    manufacturer = Column(String)
    completeness = Column(String)
    createdOn = Column(String)
    changedOn = Column(String)
    publishedOn = Column(String)
    serialNumber = Column(String)
    batchNumber = Column(String)
    tagNumber = Column(String)
    lifeCycle = Column(String)
    lifeCycleDescription = Column(String)
    source = Column(String)
    imageURL = Column(String)
    operator = Column(String)
    coordinates = Column(String)
    installationDate = Column(String)
    flocStatus = Column(String)
    buildDate = Column(String)
    isOperatorValid = Column(String)
    modelVersion = Column(String)
    soldTo = Column(String)
    image = Column(String)
    consume = Column(String)
    dealer = Column(String)
    serviceProvider = Column(String)
    primaryExternalId = Column(String)
    flocSearchTerms = Column(String)
    sourceSearchTerms = Column(String)
    manufacturerSearchTerms = Column(String)
    operatorSearchTerms = Column(String)
    class_ = Column(String)


class BaseModelTemplates(Base):
    __abstract__ = True
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    name = Column(String)
    internalId = Column(String)
    organizationID = Column(String)
    generation = Column(String)
    releaseDate = Column(String)
    serviceExpirationDate = Column(String)
    calibrationDate = Column(String)
    orderStopDate = Column(String)
    noSparePartsDate = Column(String)
    globalId = Column(String)
    image = Column(String)
    keywords = Column(String)
    safetyRiskCode = Column(String)
    descriptions = Column(String)
    manufacturerPartNumber = Column(String)
    originalManufacturerPartNumber = Column(String)
    equipmentTracking = Column(String)
    gtin = Column(String)
    brand = Column(String)
    isFirmwareCompatible = Column(String)
    modelId = Column(String)
    templateId = Column(String)
    completeness = Column(String)
    subclass = Column(String)
    modelTemplate = Column(String)
    classId = Column(String)
    subclassId = Column(String)
    hasInRevision = Column(String)
    status = Column(String)
    version = Column(String)
    publishedOn = Column(String)
    manufacturer = Column(String)
    isManufacturerValid = Column(String)
    modelType = Column(String)
    countryCode = Column(String)
    referenceId = Column(String)
    templatesDetails = Column(String)
    _class = Column(String)
    description_language = Column(String)
    description_short = Column(String)
    description_long = Column(String)
    adminData_createdBy = Column(String)
    adminData_createdOn = Column(String)
    adminData_changedBy = Column(String)
    adminData_changedOn = Column(String)
    sectionCompleteness_headerPercentage = Column(String)
    sectionCompleteness_attachmentPercentage = Column(String)
    sectionCompleteness_instructionPercentage = Column(String)
    sectionCompleteness_valuePercentage = Column(String)
    templates_id = Column(String)
    templates_primary = Column(String)


class EquModelTemplates(BaseModelTemplates):
    __tablename__ = "T_PAI_EQU_MODEL_TEMPLATES"


class FlocModelTemplates(BaseModelTemplates):
    __tablename__ = "T_PAI_FLOC_MODEL_TEMPLATES"


class EquTemplateHeader(Base):
    __tablename__ = "T_PAI_EQU_TEMPLATE_HEADER"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    templateId = Column(String)
    descriptions = Column(String)
    internalId = Column(String)
    industryStandards = Column(String)
    semanticReferences = Column(String)
    client = Column(String)
    id = Column(String)
    type = Column(String)
    source = Column(String)
    isSourceActive = Column(String)
    modelUnits = Column(String)
    typeCode = Column(String)
    hasStructure = Column(String)
    isUsed = Column(String)
    writePrivilege = Column(String)
    deletePrivilege = Column(String)
    attributeGroups = Column(String)
    indicatorGroups = Column(String)
    nestedStructures = Column(String)
    attributes = Column(String)
    indicators = Column(String)
    description_language = Column(String)
    description_short = Column(String)
    description_long = Column(String)
    parentId = Column(String)


class FlocTemplateHeader(Base):
    __tablename__ = "T_PAI_FLOC_TEMPLATE_HEADER"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    templateId = Column(String)
    descriptions = Column(String)
    internalId = Column(String)
    industryStandards = Column(String)
    semanticReferences = Column(String)
    client = Column(String)
    flocId = Column(String)
    type = Column(String)
    source = Column(String)
    isSourceActive = Column(String)
    modelUnits = Column(String)
    typeCode = Column(String)
    hasStructure = Column(String)
    isUsed = Column(String)
    writePrivilege = Column(String)
    deletePrivilege = Column(String)
    attributeGroups = Column(String)
    indicatorGroups = Column(String)
    nestedStructures = Column(String)
    attributes = Column(String)
    indicators = Column(String)
    description_language = Column(String)
    description_short = Column(String)
    description_long = Column(String)


class EquIndicatorGroups(Base):
    __tablename__ = "T_PAI_EQU_INDICATOR_GROUPS"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    templateId = Column(String)
    id = Column(String)
    indicatorGroups_descriptions = Column(String)
    indicatorGroups_internalId = Column(String)
    indicatorGroups_industryStandards = Column(String)
    indicatorGroups_semanticReferences = Column(String)
    indicatorGroups_isGlobal = Column(String)
    indicatorGroups_hasMultipleCardinality = Column(String)
    indicatorGroups_client = Column(String)
    indicatorGroups_id = Column(String)
    indicatorGroups_attributes = Column(String)
    indicatorGroups_isUsed = Column(String)
    indicatorGroups_writePrivilege = Column(String)
    indicatorGroups_deletePrivilege = Column(String)
    indicatorGroups_indicators = Column(String)
    indicatorGroups_indicatorIDs = Column(String)
    indicatorGroups_indicatorsGroupIDs = Column(String)
    indicatorGroups_isIndicator = Column(String)
    indicatorGroups_description_language = Column(String)
    indicatorGroups_description_short = Column(String)
    indicatorGroups_description_long = Column(String)
    indicatorGroups_adminData_createdBy = Column(String)
    indicatorGroups_adminData_changedBy = Column(String)


class FlocIndicatorGroups(Base):
    __tablename__ = "T_PAI_FLOC_INDICATOR_GROUPS"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    templateId = Column(String)
    flocId = Column(String)
    indicatorGroups_descriptions = Column(String)
    indicatorGroups_internalId = Column(String)
    indicatorGroups_industryStandards = Column(String)
    indicatorGroups_semanticReferences = Column(String)
    indicatorGroups_isGlobal = Column(String)
    indicatorGroups_hasMultipleCardinality = Column(String)
    indicatorGroups_client = Column(String)
    indicatorGroups_id = Column(String)
    indicatorGroups_attributes = Column(String)
    indicatorGroups_isUsed = Column(String)
    indicatorGroups_writePrivilege = Column(String)
    indicatorGroups_deletePrivilege = Column(String)
    indicatorGroups_indicators = Column(String)
    indicatorGroups_indicatorIDs = Column(String)
    indicatorGroups_indicatorsGroupIDs = Column(String)
    indicatorGroups_isIndicator = Column(String)
    indicatorGroups_description_language = Column(String)
    indicatorGroups_description_short = Column(String)
    indicatorGroups_description_long = Column(String)
    indicatorGroups_adminData_createdBy = Column(String)
    indicatorGroups_adminData_changedBy = Column(String)


class EquIndicators(Base):
    __tablename__ = "T_PAI_EQU_INDICATORS"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    templateId = Column(String)
    id = Column(String)
    indicatorGroups_id = Column(String)
    indicatorGroups_internalId = Column(String)
    indicators_descriptions = Column(String)
    indicators_internalId = Column(String)
    indicators_industryStandards = Column(String)
    indicators_semanticReferences = Column(String)
    indicators_dataType = Column(String)
    indicators_dimension1 = Column(String)
    indicators_isGlobal = Column(String)
    indicators_scale = Column(String)
    indicators_precision = Column(String)
    indicators_allowAdditionalValues = Column(String)
    indicators_codeListID = Column(String)
    indicators_expectedBehaviour = Column(String)
    indicators_aggregationConcept = Column(String)
    indicators_indicatorUom = Column(String)
    indicators_displayUom = Column(String)
    indicators_indicatorCategory = Column(String)
    indicators_indicatorColorCode = Column(String)
    indicators_indicatorType = Column(String)
    indicators_expBehaviourDesc = Column(String)
    indicators_aggConceptDesc = Column(String)
    indicators_client = Column(String)
    indicators_id = Column(String)
    indicators_dimension1Description = Column(String)
    indicators_unitOfMeasure1 = Column(String)
    indicators_dataTypeDescription = Column(String)
    indicators_isUsed = Column(String)
    indicators_writePrivilege = Column(String)
    indicators_deletePrivilege = Column(String)
    indicators_codeListDEPRECATED = Column(String)
    indicators_codeList = Column(String)
    indicators_indicatorCategoryDescription = Column(String)
    indicators_namedAssociation = Column(String)
    indicators_description_language = Column(String)
    indicators_description_short = Column(String)
    indicators_description_long = Column(String)
    indicators_codeList_description_language = Column(String)
    indicators_codeList_description_short = Column(String)
    indicators_codeList_description_long = Column(String)
    indicators_codeList_descriptions = Column(String)
    indicators_codeList_internalId = Column(String)
    indicators_codeList_industryStandards = Column(String)
    indicators_codeList_semanticReferences = Column(String)
    indicators_codeList_dataType = Column(String)
    indicators_codeList_items = Column(String)
    indicators_codeList_precision = Column(String)
    indicators_codeList_scale = Column(String)
    indicators_codeList_id = Column(String)
    indicators_codeList_isUsed = Column(String)
    indicators_codeList_writePrivilege = Column(String)
    indicators_codeList_deletePrivilege = Column(String)
    indicators_codeList_dataTypeDescription = Column(String)


class FlocIndicators(Base):
    __tablename__ = "T_PAI_FLOC_INDICATORS"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    templateId = Column(String)
    flocId = Column(String)
    indicatorGroups_id = Column(String)
    indicatorGroups_internalId = Column(String)
    indicators_descriptions = Column(String)
    indicators_internalId = Column(String)
    indicators_industryStandards = Column(String)
    indicators_semanticReferences = Column(String)
    indicators_dataType = Column(String)
    indicators_dimension1 = Column(String)
    indicators_isGlobal = Column(String)
    indicators_scale = Column(String)
    indicators_precision = Column(String)
    indicators_allowAdditionalValues = Column(String)
    indicators_codeListID = Column(String)
    indicators_expectedBehaviour = Column(String)
    indicators_aggregationConcept = Column(String)
    indicators_indicatorUom = Column(String)
    indicators_displayUom = Column(String)
    indicators_indicatorCategory = Column(String)
    indicators_indicatorColorCode = Column(String)
    indicators_indicatorType = Column(String)
    indicators_expBehaviourDesc = Column(String)
    indicators_aggConceptDesc = Column(String)
    indicators_client = Column(String)
    indicators_id = Column(String)
    indicators_dimension1Description = Column(String)
    indicators_unitOfMeasure1 = Column(String)
    indicators_dataTypeDescription = Column(String)
    indicators_isUsed = Column(String)
    indicators_writePrivilege = Column(String)
    indicators_deletePrivilege = Column(String)
    indicators_codeListDEPRECATED = Column(String)
    indicators_codeList = Column(String)
    indicators_indicatorCategoryDescription = Column(String)
    indicators_namedAssociation = Column(String)
    indicators_description_language = Column(String)
    indicators_description_short = Column(String)
    indicators_description_long = Column(String)


class ERPCharacteristics(Base):

    __tablename__ = "T_ERP_CHARACTERISTICS"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    Delete_mc = Column(String)
    Update_mc = Column(String)
    to_CharacteristicDesc_oc = Column(String)
    to_CharacteristicReference_oc = Column(String)
    to_CharacteristicRestriction_oc = Column(String)
    to_CharacteristicValue_oc = Column(String)
    CharcInternalID = Column(String)
    Characteristic = Column(String)
    CharcStatus = Column(String)
    CharcStatusName = Column(String)
    CharcDataType = Column(String)
    CharcLength = Column(String)
    CharcDecimals = Column(String)
    CharcTemplate = Column(String)
    ValueIsCaseSensitive = Column(String)
    CharcGroup = Column(String)
    CharcGroupName = Column(String)
    EntryIsRequired = Column(String)
    MultipleValuesAreAllowed = Column(String)
    CharcValueUnit = Column(String)
    UnitOfMeasureISOCode = Column(String)
    Currency = Column(String)
    CurrencyISOCode = Column(String)
    CharcExponentValue = Column(String)
    ValueIntervalIsAllowed = Column(String)
    AdditionalValueIsAllowed = Column(String)
    NegativeValueIsAllowed = Column(String)
    ValidityStartDate = Column(String)
    ValidityEndDate = Column(String)
    ChangeNumber = Column(String)
    DocumentType = Column(String)
    DocNumber = Column(String)
    DocumentVersion = Column(String)
    DocumentPart = Column(String)
    CharcMaintAuthGrp = Column(String)
    CharcIsReadOnly = Column(String)
    CharcIsHidden = Column(String)
    CharcIsRestrictable = Column(String)
    CharcExponentFormat = Column(String)
    CharcEntryIsNotFormatCtrld = Column(String)
    CharcTemplateIsDisplayed = Column(String)
    CreationDate = Column(String)
    LastChangeDate = Column(String)
    CharcLastChangedDateTime = Column(String)
    KeyDate = Column(String)
    metadata_id = Column(String)
    metadata_uri = Column(String)
    metadata_type = Column(String)
    metadata_etag = Column(String)
    to_CharacteristicDesc___deferred_uri = Column(String)
    to_CharacteristicReference___deferred_uri = Column(String)
    to_CharacteristicRestriction___deferred_uri = Column(String)
    to_CharacteristicValue___deferred_uri = Column(String)


class PreLoadIndicators(Base):
    __tablename__ = "T_PRE_LOAD_INDICATORS"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    internalId = Column(String)
    name = Column(String)
    externalId = Column(String)
    objectType = Column(String)
    indicatorGroups_internalId = Column(String)
    indicatorGroups_description_short = Column(String)
    indicators_internalId = Column(String)
    indicators_description_short = Column(String)
    indicators_datatype = Column(String)
    indicators_scale = Column(String)
    indicators_precision = Column(String)
    id = Column(String)
    templateId = Column(String)
    indicatorGroups_id = Column(String)
    indicators_id = Column(String)
    ERPCharacteristic = Column(String)
    CharcInternalID = Column(String)
    APMIndicatorCategory = Column(String)
    apm_guid = Column(String)
    ssid = Column(String)
    technicalObject_type = Column(String)
    valid = Column(String)


class LoadIndicators(Base):
    __tablename__ = "T_LOAD_INDICATORS"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    technicalObject_number = Column(String)
    technicalObject_type = Column(String)
    technicalObject_SSID = Column(String)
    category_name = Column(String)
    category_SSID = Column(String)
    characteristics_characteristicsInternalId = Column(String)
    characteristics_SSID = Column(String)
    positionDetails_ID = Column(String)
    valid = Column(String)


class PostLoadIndicators(Base):
    __tablename__ = "T_POST_LOAD_INDICATORS"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    ID = Column(String)
    createdAt = Column(String)
    createdBy = Column(String)
    modifiedAt = Column(String)
    modifiedBy = Column(String)
    measuringPointId = Column(String)
    technicalObject_number = Column(String)
    technicalObject_SSID = Column(String)
    technicalObject_type = Column(String)
    technicalObject_technicalObject = Column(String)
    category_SSID = Column(String)
    category_name = Column(String)
    characteristics_SSID = Column(String)
    characteristics_characteristicsInternalId = Column(String)
    positionDetails_ID = Column(String)
    minValue = Column(String)
    maxValue = Column(String)
    targetValue = Column(String)
    color = Column(String)
    decimalDisplay = Column(String)
    type = Column(String)
    calculationType = Column(String)
    source = Column(String)


# ---------------------------------------------------------------------------------------------------------------------------- #
# Models: View
# ---------------------------------------------------------------------------------------------------------------------------- #


class TransformIndicators:
    tenantid = Column(String)
    internalId = Column(String)
    type = Column(String)
    name = Column(String)

    # >>>>> External Data <<<<<
    externalId = Column(String)
    objectType = Column(String)

    # >>>>> Indicator Groups / APM Indicator Position <<<<<
    indicatorGroups_internalId = Column(String)
    indicatorGroups_description_short = Column(String)

    # >>>>> Indicators / ERP Characteristic<<<<<
    indicators_internalId = Column(String)
    indicators_description_short = Column(String)
    indicators_dataType = Column(String)
    indicators_scale = Column(String)
    indicators_precision = Column(String)

    # >>>>> Reference Fields (GUIDs) <<<<<
    id = Column(String)
    templateId = Column(String)
    indicatorGroups_id = Column(String)
    indicators_id = Column(String)
    valid = Column(String)


class BaseView_TransformIndicators(TransformIndicators):
    __abstract__ = True
    __table_args__ = (
        PrimaryKeyConstraint(
            "tenantid", "id", "templateId", "indicatorGroups_id", "indicators_id"
        ),
    )

    @classmethod
    def definition(cls, type, ExternalData, IndicatorGroups, Indicators):
        __definition__ = (
            select(
                ExternalData.tenantid.label("tenantid"),
                ExternalData.internalId,
                literal_column(f"'{type}'").label("type"),
                ExternalData.name,
                # >>>>> External Data <<<<<
                ExternalData.externalId,
                ExternalData.objectType,
                # >>>>> Indicator Groups / APM Indicator Position <<<<<
                IndicatorGroups.indicatorGroups_internalId,
                IndicatorGroups.indicatorGroups_description_short,
                Indicators.indicators_internalId,
                Indicators.indicators_description_short,
                Indicators.indicators_dataType,
                Indicators.indicators_scale,
                Indicators.indicators_precision,
                # >>>>> Reference Fields (GUIDs) <<<<<
                ExternalData.id,
                ExternalData.templateId,
                IndicatorGroups.indicatorGroups_id,
                Indicators.indicators_id,
                case(
                    (
                        Indicators.indicators_id.isnot(None)
                        & IndicatorGroups.indicatorGroups_id.isnot(None),
                        "X",
                    ),
                    else_=None,
                ).label("valid"),
            )
            .select_from(ExternalData)
            .outerjoin(
                IndicatorGroups,
                (ExternalData.tenantid == IndicatorGroups.tenantid)
                & (ExternalData.templateId == IndicatorGroups.templateId),
            )
            .outerjoin(
                Indicators,
                (Indicators.tenantid == ExternalData.tenantid)
                & (Indicators.templateId == ExternalData.templateId)
                & (Indicators.indicatorGroups_id == IndicatorGroups.indicatorGroups_id),
            )
            .where(ExternalData.valid == "X")
        )

        return __definition__


class V_PAI_EquipmentExternalData(ViewBase):
    __tablename__ = "V_PAI_EQU_EXTERNAL_DATA"

    tenantid = Column(String)
    id = Column(String)
    name = Column(String)
    internalId = Column(String)
    status = Column(String)
    statusDescription = Column(String)
    version = Column(String)
    hasInRevision = Column(String)
    modelId = Column(String)
    modelName = Column(String)
    shortDescription = Column(String)
    templateId = Column(String)
    modelTemplate = Column(String)
    modelVersion = Column(String)
    externalId = Column(String)
    objectType = Column(String)
    systemType = Column(String)
    systemName = Column(String)
    externalObjectTypeCode = Column(String)
    valid = Column(String)

    __table_args__ = (PrimaryKeyConstraint("tenantid", "id"),)

    __definition__ = (
        select(
            EquipmentHeader.tenantid,
            EquipmentHeader.equipmentId.label("id"),
            EquipmentHeader.name,
            EquipmentHeader.internalId,
            EquipmentHeader.status,
            EquipmentHeader.statusDescription,
            EquipmentHeader.version,
            EquipmentHeader.hasInRevision,
            EquipmentHeader.modelId,
            EquipmentHeader.modelName,
            EquipmentHeader.shortDescription,
            EquModelTemplates.templates_id.label("templateId"),
            EquipmentHeader.modelTemplate,
            EquipmentHeader.modelVersion,
            ExternalData_EQU.externalId,
            ExternalData_EQU.objectType,
            ExternalData_EQU.systemType,
            ExternalData_EQU.systemName,
            ExternalData_EQU.externalObjectTypeCode,
            case((ExternalData_EQU.externalId.isnot(None), "X"), else_="").label(
                "valid"
            ),
        )
        .select_from(EquipmentHeader)
        .outerjoin(
            EquModelTemplates,
            (EquModelTemplates.tenantid == EquipmentHeader.tenantid)
            & (EquModelTemplates.modelId == EquipmentHeader.modelId),
        )
        .outerjoin(
            ExternalData_EQU,
            (ExternalData_EQU.ainObjectId == EquipmentHeader.equipmentId)
            & (ExternalData_EQU.tenantid == EquipmentHeader.tenantid),
        )
        .order_by(EquipmentHeader.internalId)
    )


class V_Transform_EquIndicators(ViewBase, BaseView_TransformIndicators):
    __tablename__ = "V_TRANSFORM_EQU_INDICATORS"
    __definition__ = BaseView_TransformIndicators.definition(
        type="EQU",
        ExternalData=V_PAI_EquipmentExternalData,
        IndicatorGroups=EquIndicatorGroups,
        Indicators=EquIndicators,
    )


class T_UDR_Indicators(Base, TransformIndicators):
    __tablename__ = "T_UDR_APM_INDICATORS"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    propose_APMIndicatorPosition = Column(String)
    input_APMIndicatorPosition = Column(String)
    APMIndicatorPosition = Column(String)
    APMIndicatorPosition_src = Column(String)

    propose_ERPCharacteristic = Column(String)
    input_ERPCharacteristic = Column(String)
    ERPCharacteristic = Column(String)
    ERPCharacteristic_src = Column(String)

    propose_APMIndicatorCategory = Column(String)
    input_APMIndicatorCategory = Column(String)
    APMIndicatorCategory = Column(String)
    APMIndicatorCategory_src = Column(String)


class V_APMIndicatorPositions(ViewBase):
    __tablename__ = "V_APM_INDICATOR_POSITIONS"

    idx = Column(Integer, primary_key=True)
    tenantid = Column(String)
    indicatorGroups_internalId = Column(String)
    indicatorGroups_description_short = Column(String)
    APMIndicatorPosition = Column(String)
    APMIndicatorPosition_src = Column(String)
    name = Column(String)
    ssid = Column(String)
    apm_guid = Column(String)

    __definition__ = (
        select(
            T_UDR_Indicators.idx,
            T_UDR_Indicators.tenantid,
            T_UDR_Indicators.indicatorGroups_internalId,
            T_UDR_Indicators.indicatorGroups_description_short,
            T_UDR_Indicators.APMIndicatorPosition,
            T_UDR_Indicators.APMIndicatorPosition_src,
            APM_IndicatorPositions.name,
            APM_IndicatorPositions.SSID,
            APM_IndicatorPositions.ID.label("apm_guid"),
        )
        .select_from(T_UDR_Indicators)
        .outerjoin(
            APM_IndicatorPositions,
            (
                func.upper(APM_IndicatorPositions.name)
                == func.upper(T_UDR_Indicators.APMIndicatorPosition)
            )
            & (APM_IndicatorPositions.tenantid == T_UDR_Indicators.tenantid),
        )
        .order_by(
            T_UDR_Indicators.APMIndicatorPosition_src,
            T_UDR_Indicators.APMIndicatorPosition,
        )
    )


class V_ERPCharacteristics(ViewBase):
    __tablename__ = "V_ERP_CHARACTERISTICS"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    tenantid = Column(String)
    indicators_datatype = Column(String)
    indicators_scale = Column(String)
    indicators_precision = Column(String)
    ERPCharacteristic = Column(String)
    ERPCharacteristic_src = Column(String)
    CharcInternalID = Column(String)

    __definition__ = (
        select(
            T_UDR_Indicators.idx,
            T_UDR_Indicators.tenantid,
            T_UDR_Indicators.indicators_dataType,
            T_UDR_Indicators.indicators_scale,
            T_UDR_Indicators.indicators_precision,
            T_UDR_Indicators.ERPCharacteristic,
            T_UDR_Indicators.ERPCharacteristic_src,
            ERPCharacteristics.CharcInternalID,
        )
        .select_from(T_UDR_Indicators)
        .outerjoin(
            ERPCharacteristics,
            (
                func.upper(ERPCharacteristics.Characteristic)
                == func.upper(T_UDR_Indicators.ERPCharacteristic)
            )
            & (ERPCharacteristics.tenantid == T_UDR_Indicators.tenantid),
        )
        .group_by(T_UDR_Indicators.ERPCharacteristic)
        .order_by(
            T_UDR_Indicators.ERPCharacteristic_src,
            T_UDR_Indicators.ERPCharacteristic,
        )
    )


class V_PAI_FlocExternalData(ViewBase):
    __tablename__ = "V_PAI_FLOC_EXTERNAL_DATA"

    tenantid = Column(String)
    id = Column(String)
    name = Column(String)
    internalId = Column(String)
    status = Column(String)
    statusDescription = Column(String)
    version = Column(String)
    hasInRevision = Column(String)
    modelId = Column(String)
    modelName = Column(String)
    shortDescription = Column(String)
    templateId = Column(String)
    modelTemplate = Column(String)
    modelVersion = Column(String)
    externalId = Column(String)
    objectType = Column(String)
    systemType = Column(String)
    systemName = Column(String)
    externalObjectTypeCode = Column(String)
    valid = Column(String)

    __table_args__ = (PrimaryKeyConstraint("tenantid", "id"),)

    __definition__ = (
        select(
            FlocHeader.tenantid,
            FlocHeader.id,
            FlocHeader.name,
            FlocHeader.internalId,
            FlocHeader.status,
            FlocHeader.statusDescription,
            FlocHeader.version,
            FlocHeader.hasInRevision,
            FlocHeader.modelId,
            FlocHeader.modelName,
            FlocHeader.shortDescription,
            FlocHeader.templateId,
            FlocHeader.modelTemplate,
            FlocHeader.modelVersion,
            ExternalData_FLOC.externalId,
            ExternalData_FLOC.objectType,
            ExternalData_FLOC.systemType,
            ExternalData_FLOC.systemName,
            ExternalData_FLOC.externalObjectTypeCode,
            case((ExternalData_FLOC.externalId.isnot(None), "X"), else_="").label(
                "valid"
            ),
        )
        .select_from(FlocHeader)
        .outerjoin(
            ExternalData_FLOC,
            (ExternalData_FLOC.ainObjectId == FlocHeader.id)
            & (ExternalData_FLOC.tenantid == FlocHeader.tenantid),
        )
        .order_by(FlocHeader.internalId)
    )


class V_Transform_FlocIndicators(ViewBase, BaseView_TransformIndicators):
    __tablename__ = "V_TRANSFORM_FLOC_INDICATORS"
    __definition__ = BaseView_TransformIndicators.definition(
        type="FLOC",
        ExternalData=V_PAI_FlocExternalData,
        IndicatorGroups=FlocIndicatorGroups,
        Indicators=FlocIndicators,
    )


class V_Transform_Indicators(ViewBase, BaseView_TransformIndicators):
    __tablename__ = "V_TRANSFORM_INDICATORS"
    __definition__ = (
        select("*")
        .select_from(V_Transform_FlocIndicators)
        .where(V_Transform_FlocIndicators.valid == "X")
    ).union_all(
        select("*")
        .select_from(V_Transform_EquIndicators)
        .where(V_Transform_EquIndicators.valid == "X")
    )


class V_PostLoad_Indicators(ViewBase):

    __tablename__ = "V_POST_LOAD_INDICATORS"

    tenantid = Column(String)
    internalId = Column(String)
    name = Column(String)
    externalId = Column(String)
    objectType = Column(String)
    indicatorGroups_internalId = Column(String)
    indicatorGroups_description_short = Column(String)
    indicators_internalId = Column(String)
    indicators_description_short = Column(String)
    indicators_datatype = Column(String)
    indicators_scale = Column(String)
    indicators_precision = Column(String)
    id = Column(String)
    templateId = Column(String)
    indicatorGroups_id = Column(String)
    indicators_id = Column(String)
    ERPCharacteristic = Column(String)
    CharcInternalID = Column(String)
    APMIndicatorCategory = Column(String)
    apm_positionId = Column(String)
    ssid = Column(String)
    technicalObject_type = Column(String)
    valid = Column(String)
    apm_indicatorId = Column(String)

    __table_args__ = (
        PrimaryKeyConstraint(
            "tenantid",
            "id",
            "templateId",
            "indicatorGroups_id",
            "indicators_id",
            "ERPCharacteristic",
            "CharcInternalID",
            "APMIndicatorCategory",
            "apm_positionId",
            "ssid",
            "technicalObject_type",
        ),
    )

    __definition__ = (
        select(
            PreLoadIndicators.tenantid,
            PreLoadIndicators.internalId,
            PreLoadIndicators.name,
            PreLoadIndicators.externalId,
            PreLoadIndicators.objectType,
            PreLoadIndicators.indicatorGroups_internalId,
            PreLoadIndicators.indicatorGroups_description_short,
            PreLoadIndicators.indicators_internalId,
            PreLoadIndicators.indicators_description_short,
            PreLoadIndicators.indicators_datatype,
            PreLoadIndicators.indicators_scale,
            PreLoadIndicators.indicators_precision,
            PreLoadIndicators.id,
            PreLoadIndicators.templateId,
            PreLoadIndicators.indicatorGroups_id,
            PreLoadIndicators.indicators_id,
            PreLoadIndicators.ERPCharacteristic,
            PreLoadIndicators.CharcInternalID,
            PreLoadIndicators.APMIndicatorCategory,
            PreLoadIndicators.apm_guid.label("apm_positionId"),
            PreLoadIndicators.ssid,
            PreLoadIndicators.technicalObject_type,
            PreLoadIndicators.valid,
            PostLoadIndicators.ID.label("apm_indicatorId"),
        )
        .select_from(PreLoadIndicators)
        .outerjoin(
            PostLoadIndicators,
            (PreLoadIndicators.tenantid == PostLoadIndicators.tenantid)
            & (
                PreLoadIndicators.externalId
                == PostLoadIndicators.technicalObject_number
            )
            & (
                PreLoadIndicators.CharcInternalID
                == PostLoadIndicators.characteristics_characteristicsInternalId
            )
            & (
                PreLoadIndicators.APMIndicatorCategory
                == PostLoadIndicators.category_name
            )
            & (PreLoadIndicators.apm_guid == PostLoadIndicators.positionDetails_ID)
            & (PreLoadIndicators.ssid == PostLoadIndicators.category_SSID)
            & (PreLoadIndicators.ssid == PostLoadIndicators.characteristics_SSID)
            & (
                PreLoadIndicators.technicalObject_type
                == PostLoadIndicators.technicalObject_type
            ),
        )
    )
