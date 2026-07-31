from app import app

client = app.test_client()
root = client.get('/')
print('HOME', root.status_code, 'NxtHealth' in root.get_data(as_text=True))
response = client.post('/api/analyze', json={'symptoms': 'fever and cough', 'age': 30, 'language': 'en'})
print('ANALYZE', response.status_code)
print(response.get_json()['analysis']['severity'])
print(response.get_json()['analysis']['diagnosis'])
