from main import forecast_point_one_day

# Test trực tiếp (bỏ qua HTTP request)
result = forecast_point_one_day(place="Hanoi", date="2025-10-05")
print(result)
