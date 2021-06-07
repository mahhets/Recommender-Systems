import pandas as pd
import numpy as np


def prefilter_items(data, take_n_popular=5000, item_features=None,
                    min_items_in_department=10, max_price=100, min_price=1):
    """
    Начальная фильтрация товаров
    :param data: подается pandas.DataFrame
    :param take_n_popular: число популярных покупок для отбора
    :param item_features: таблица признаков товаров
    :param min_items_in_department: минимальное число товаров в отделе
    :param max_price: максимальная цена для отбора
    :param min_price: минимальная цена для отбора
    :return: выборка после фильтрации
    """

    n_items_before = data['item_id'].nunique()

    popularity = data.groupby('item_id')['user_id'].nunique().reset_index() / data['user_id'].nunique()
    popularity.rename(columns={'user_id': 'share_unique_users'}, inplace=True)

    # Уберем самые популярные товары (их и так купят)
    # top_popular = popularity[popularity['share_unique_users'] > 0.2]['item_id']
    # data = data[~data['item_id'].isin(top_popular)]

    # Уберем самые НЕ популярные товары (их и так НЕ купят)
    top_unpopular = popularity[popularity['share_unique_users'] < 0.0005]['item_id']
    data = data[~data['item_id'].isin(top_unpopular)]

    # Уберем товары, которые не продавались за последние 12 месяцев

    # Уберем не интересные для рекоммендаций категории (department). Менее 10 наименований в кагегории
    if item_features is not None:
        department_size = item_features.groupby(by='department').nunique()['item_id'] \
            .sort_values(ascending=False).reset_index() \
            .rename(columns={'item_id': 'n_items'})

        rare_departments = department_size.loc[
            department_size['n_items'] <= min_items_in_department, 'department'].tolist()
        items_in_rare_departments = item_features.loc[
            item_features['department'].isin(rare_departments), 'item_id'].unique().tolist()

        data = data[~data['item_id'].isin(items_in_rare_departments)]
    # Уберем нулевые продажи
    data = data[data['quantity'] != 0]

    # Уберем слишком дешевые товары (на них не заработаем). 1 покупка из рассылок стоит 60 руб.
    data['price'] = (data['sales_value'] -
                     data['retail_disc'] -
                     data['coupon_disc'] -
                     data['coupon_match_disc']) / (np.maximum(data['quantity'], 1))
    # data = data[data['price'] > min_price]

    # Уберем слишком дорогие товары
    data = data[data['price'] < max_price]

    # Возьмем топ по популярности
    popularity = data.groupby('item_id')['quantity'].sum().reset_index()
    popularity.rename(columns={'quantity': 'n_sold'}, inplace=True)

    top = popularity.sort_values('n_sold', ascending=False).head(take_n_popular).item_id.tolist()

    # Заведем фиктивный item_id (если юзер покупал товары из топ-5000, то он "купил" такой товар)
    data.loc[~data['item_id'].isin(top), 'item_id'] = 999999

    # ...

    n_items_after = data['item_id'].nunique()
    print(f'Ввборка уменьшена с {n_items_before} до {n_items_after} товаров')

    return data


def postfilter_items(user_id, recommednations):
    pass