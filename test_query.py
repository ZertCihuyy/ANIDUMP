import requests
API_URL = 'https://graphql.anilist.co'
query = '''
query {
  Page(page: 1, perPage: 5) {
    media(type: ANIME, sort: UPDATED_AT_DESC) {
      id
      updatedAt
    }
  }
}
'''
response = requests.post(API_URL, json={'query': query})
print(response.json())
