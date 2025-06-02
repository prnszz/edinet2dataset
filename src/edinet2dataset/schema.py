from dataclasses import dataclass, asdict


@dataclass
class Parameter:
    date: str
    type: str


@dataclass
class Resultset:
    count: int


# e.g. {'metadata': {'title': '提出された書類を把握するためのAPI', 'parameter': {'date': '2024-11-01', 'type': '1'}, 'resultset': {'count': 320}, 'processDateTime': '2024-12-16 00:00', 'status': '200', 'message': 'OK'}}
@dataclass
class Metadata:
    title: str
    parameter: Parameter
    resultset: Resultset
    processDateTime: str
    status: str
    message: str

    def __init__(self, json_data):
        self.title = json_data["metadata"]["title"]
        self.parameter = Parameter(
            json_data["metadata"]["parameter"]["date"],
            json_data["metadata"]["parameter"]["type"],
        )
        self.resultset = Resultset(json_data["metadata"]["resultset"]["count"])
        self.processDateTime = json_data["metadata"]["processDateTime"]
        self.status = json_data["metadata"]["status"]
        self.message = json_data["metadata"]["message"]


# e.g. {'seqNumber': 1, 'docID': 'S100UKYJ', 'edinetCode': 'E01428', 'secCode': '79390', 'JCN': '9240001003119', 'filerName': '株式会社研創', 'fundCode': None, 'ordinanceCode': '010', 'formCode': '043A00', 'docTypeCode': '160', 'periodStart': '2024-04-01', 'periodEnd': '2025-03-31', 'submitDateTime': '2024-11-01 09:00', 'docDescription': '半期報告書－第54期(2024/04/01－2025/03/31)', 'issuerEdinetCode': None, 'subjectEdinetCode': None, 'subsidiaryEdinetCode': None, 'currentReportReason': None, 'parentDocID': None, 'opeDateTime': None, 'withdrawalStatus': '0', 'docInfoEditStatus': '0', 'disclosureStatus': '0', 'xbrlFlag': '1', 'pdfFlag': '1', 'attachDocFlag': '0', 'englishDocFlag': '0', 'csvFlag': '1', 'legalStatus': '1'}
@dataclass
class Result:
    seqNumber: int
    docID: str
    edinetCode: str
    secCode: str
    JCN: str
    filerName: str
    fundCode: str
    ordinanceCode: str
    formCode: str
    docTypeCode: str
    periodStart: str
    periodEnd: str
    submitDateTime: str
    docDescription: str
    issuerEdinetCode: str
    subjectEdinetCode: str
    subsidiaryEdinetCode: str
    currentReportReason: str
    parentDocID: str
    opeDateTime: str
    withdrawalStatus: str
    docInfoEditStatus: str
    disclosureStatus: str
    xbrlFlag: str
    pdfFlag: str
    attachDocFlag: str
    englishDocFlag: str
    csvFlag: str
    legalStatus: str

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(**json_data)

    def to_dict(self):
        return asdict(self)


def test_result():
    result = {
        "seqNumber": 1,
        "docID": "S100UKYJ",
        "edinetCode": "E01428",
        "secCode": "79390",
        "JCN": "9240001003119",
        "filerName": "株式会社研創",
        "fundCode": None,
        "ordinanceCode": "010",
        "formCode": "043A00",
        "docTypeCode": "160",
        "periodStart": "2024-04-01",
        "periodEnd": "2025-03-31",
        "submitDateTime": "2024-11-01 09:00",
        "docDescription": "半期報告書－第54期(2024/04/01－2025/03/31)",
        "issuerEdinetCode": None,
        "subjectEdinetCode": None,
        "subsidiaryEdinetCode": None,
        "currentReportReason": None,
        "parentDocID": None,
        "opeDateTime": None,
        "withdrawalStatus": "0",
        "docInfoEditStatus": "0",
        "disclosureStatus": "0",
        "xbrlFlag": "1",
        "pdfFlag": "1",
        "attachDocFlag": "0",
        "englishDocFlag": "0",
        "csvFlag": "1",
        "legalStatus": 1,
    }
    result_obj = Result.from_json(result)
    result_dict = result_obj.to_dict()
    assert result_dict["seqNumber"] == 1


# API response when type 2 is specified
@dataclass
class Response:
    metadata: Metadata
    results: list[Result]

    def __init__(self, json_data):
        self.metadata = Metadata(json_data)
        self.results = [Result.from_json(result) for result in json_data["results"]]
