from typing import List,Dict
from app.models import AppModel
from app.models.manifest_model import ManifestModel



def get_app_manifest(app_id:str,version:str) ->ManifestModel|None:
    from app.repositories import AppDb
    from app.services.http_service import get_http_response
    db = AppDb()
    app_item = db.get_db_item(app_id)
    if not app_item:
        print(f"Couldn't find app with id {app_id} in Database")
        return
    url = f"https://raw.githubusercontent.com/{app_item.owner}/{app_item.repo}/{version}/manifest.json"
    try:
        response = get_http_response(url)
        response_data = response.json()
        return ManifestModel.convert_data_to_manifest_model(response_data)
    except Exception as e:
        print(f"Error: failed to get manifest for app with id {app_id} and version {version}. Message: {e}")




class Apps:
    _instance = None
    _apps_dict: Dict[str,AppModel]

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._apps_dict = {}
            print("Apps instance created!")
            cls._instance.update()

    def update(self):
        from app.repositories import AppDb,InstalledApps,AppReleases
        db = AppDb()
        db_dict = db.get_db()

        for id,item in db_dict.items():
            app_releases = AppReleases(id).ge





def get_app_details(app_id:str)->AppModel|None:
    try:
        #has versions, needed for catalog
        app_versions = get_app_version_tags(app_id)
        if not app_versions:
            raise Exception("Couldn't fetch app versions")
        #has name,description,supportedOS and iconPath 
        app_manifest = get_app_manifest(app_id,app_versions[0])
        if not app_manifest:
            raise Exception("Couldn't fetch app manifest")
        #has status
        app_status = get_app_status(app_id)
        if not app_status:
            raise Exception("Couldn't fetch app status")    
        #has installed version
        installed_version = get_installed_version(app_id)
        return AppModel(name=app_manifest.name,description=app_manifest.description,versions=app_versions,
                         status=app_status,supportedOS=list(app_manifest.supportedOS.keys()),installedVersion=installed_version,iconPath=app_manifest.iconPath)
    except Exception as e:
        print(f"Couldn't get details for app with id: {app_id}. error: {e}")
        

    
def get_all_apps_details()->List[AppModel]:
    res:List[AppModel] = []
    db = get_db()
    for item in db:
        app_details = get_app_details(item.id)
        if app_details:
            res.append(app_details)
    return res

def filter_apps_by_os(res:List[AppModel])->None:
    res[:] = [app for app in res if sys.platform in app.supportedOS]



    













