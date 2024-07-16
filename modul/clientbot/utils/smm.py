# import asyncio
# import pickle
# import json
#
# from clientbot.utils.PartnerAPI import PartnerAPI
#
# from config import settings
# from clientbot.data.schemas import Service
# from clientbot import strings
# from loader import client, redis
# from transliterate import translit, detect_language
#
# async def get_order_statuses(order_ids: list):
#     orders = ','.join(map(str, order_ids))
#     async with client.session.get(url=settings.SMM_BASE_API_URL + f"&action=status&orders={orders}") as r:
#         data = json.loads(await r.text())
#         return data
#
# async def save_services() -> list[Service]:
#     services = await redis.get("services")
#     if not services:
#         partner = PartnerAPI(settings.SMM_KEY)
#         services = partner.load_services()
#         await redis.set("services", pickle.dumps(services), ex=60 * 60 * 24)
#     else:
#         services = pickle.loads(services)
#     return services
#
# async def get_services():
#     services = await redis.get("services")
#     if not services:
#         async with asyncio.Lock():
#             services = await save_services()
#     else:
#         services = pickle.loads(services)
#     return services
#
#
# async def save_categories():
#     services = await get_services()
#     categories = await redis.get("categories")
#     if not categories:
#         categories = [x.category for x in services]
#         smm_categories = {}
#         for smm_name in strings.SMM_CATEGORIES:
#             for category in categories:
#                 if smm_name not in smm_categories:
#                     smm_categories[smm_name] = []
#                 second = smm_name
#                 match detect_language(second):
#                     case 'en':
#                         second = translit(second, 'ru')
#                     case 'ru':
#                         second = translit(second, reversed=True)
#                 if (smm_name in category or second in category) and category not in smm_categories[smm_name]:
#                     smm_categories[smm_name].append(category)
#         lock = asyncio.Lock()
#         async with lock:
#             await redis.set("categories", pickle.dumps(smm_categories), ex=60 * 60 * 24)
#     else:
#         smm_categories = pickle.loads(categories)
#     return smm_categories
#
#
# async def get_categories(service_name: str):
#     categories = await redis.get("categories")
#     if not categories:
#         async with asyncio.Lock():
#             categories = await save_categories()
#     else:
#         categories = pickle.loads(categories)
#     return categories[service_name]
#
#
# async def get_category(smm_idx: int, category_idx: int):
#     smm = strings.SMM_CATEGORIES[smm_idx]
#     categories = await get_categories(smm)
#     return categories[category_idx]
#
#
# async def get_services_by_category(category_name: str):
#     services_by_category = await redis.get(f"services_by_{category_name}")
#     if not services_by_category:
#         services_by_category = [x for x in await get_services() if x.category == category_name]
#         await redis.set(f"services_by_{category_name}", pickle.dumps(services_by_category), ex=60 * 60 * 24)
#     else:
#         services_by_category = pickle.loads(services_by_category)
#     return services_by_category
#
#
# async def get_service(service_id: int) -> Service:
#     for service in await get_services():
#         if service.service == f"{service_id}":
#             return service
