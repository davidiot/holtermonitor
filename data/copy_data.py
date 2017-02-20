# we want to sample at sample at 500 Hz, but current sample is 1000 Hz


with open("pvcs.lvm") as f:
    content = f.readlines()

for x in range(23, len(content)):
    pass

size = float(content[len(content) - 1].split()[0]) + 0.001

with open("longdata.lvm", 'w') as file:
    for x in content:
        file.write(x)

    for i in range(1, 500):
        for j in range(23, len(content)):
            line = content[j]
            row = line.split()
            new_time = float(row[0]) + i * size
            space_index = line.index('	')
            file.write('{0:.6f}'.format(new_time) + line[space_index:])
