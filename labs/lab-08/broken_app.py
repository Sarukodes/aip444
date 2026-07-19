def calculate_average(total, count):
    return total / count


def prepare_report(values):
    total = sum(values)
    count = len(values)
    return calculate_average(total, count)


def generate_dashboard():
    scores = []
    return prepare_report(scores)


def main():
    result = generate_dashboard()
    print(result)


if __name__ == "__main__":
    main()