
lags = [
	{'key': '81', 'uplink_name': 'LAG-3', 'pnic': 'vmnic5'}, 
	{'key': '80', 'uplink_name': 'LAG-2', 'pnic': 'vmnic4'}, 
	 
	{'key': '78', 'uplink_name': 'LAG-0', 'pnic': None}
		]
uplinks= [
	{'key': '77', 'uplink_name': 'Uplink 3', 'pnic': None}, 
	{'key': '76', 'uplink_name': 'Uplink 2', 'pnic': None}, 
	{'key': '75', 'uplink_name': 'Uplink 1', 'pnic': 'vmnic3'}, 
	{'key': '74', 'uplink_name': 'Uplink 0', 'pnic': 'vmnic2'}
	]

for i, j in zip(lags, uplinks):
    print(i,j)
