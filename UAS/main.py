from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import tbl_gpu as tbl_gpuModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'clock_speed': 4, 'bandwith': 4, 'vram': 3, 'harga': 5, 'series': 3}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(tbl_gpuModel.nama_gpu, tbl_gpuModel.clock_speed, tbl_gpuModel.bandwith, tbl_gpuModel.vram, tbl_gpuModel.harga, tbl_gpuModel.series)
        result = session.execute(query).fetchall()
        print(result)
        return [{'nama_gpu': tbl_gpu.nama_gpu, 'clock_speed': tbl_gpu.clock_speed, 'bandwith': tbl_gpu.bandwith, 'vram': tbl_gpu.vram, 'harga': tbl_gpu.harga, 'series': tbl_gpu.series} for tbl_gpu in result]

    @property
    def normalized_data(self):
        clock_speed_values = []
        bandwith_values = []
        vram_values = []
        harga_values = []
        series_values = []

        for data in self.data:
            clock_speed_values.append(data['clock_speed'])
            bandwith_values.append(data['bandwith'])
            vram_values.append(data['vram'])
            harga_values.append(data['harga'])
            series_values.append(data['series'])

        return [
            {'nama_gpu': data['nama_gpu'],
             'clock_speed': min(clock_speed_values) / data['clock_speed'],
             'bandwith': data['bandwith'] / max(bandwith_values),
             'vram': data['vram'] / max(vram_values),
             'harga': data['harga'] / max(harga_values),
             'series': data['series'] / max(series_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
                row['clock_speed'] ** self.raw_weight['clock_speed'] *
                row['bandwith'] ** self.raw_weight['bandwith'] *
                row['vram'] ** self.raw_weight['vram'] *
                row['harga'] ** self.raw_weight['harga'] *
                row['series'] ** self.raw_weight['series']
            )

            produk.append({
                'nama_gpu': row['nama_gpu'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'nama_gpu': product['nama_gpu'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['nama_gpu']:
                  round(row['clock_speed'] * weight['clock_speed'] +
                        row['bandwith'] * weight['bandwith'] +
                        row['vram'] * weight['vram'] +
                        row['harga'] * weight['harga'] +
                        row['series'] * weight['series'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class tbl_gpu(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(tbl_gpuModel)
        data = [{'nama_gpu': tbl_gpu.nama_gpu, 'clock_speed': tbl_gpu.clock_speed, 'bandwith': tbl_gpu.bandwith, 'vram': tbl_gpu.vram, 'harga': tbl_gpu.harga, 'series': tbl_gpu.series} for tbl_gpu in session.scalars(query)]
        return self.get_paginated_result('tbl_gpu/', data, request.args), HTTPStatus.OK.value


api.add_resource(tbl_gpu, '/tbl_gpu')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)