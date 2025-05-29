// Загрузка связанных данных при изменении города
$('#city').change(function () {
  const cityId = $(this).val();
  $.getJSON('/get_city_options/' + cityId, function (data) {
    function updateSelectOptions(selectId, items) {
      const select = $('#' + selectId);
      select.empty();
      items.forEach(function (item) {
        select.append(new Option(item.name, item.id));
      });
    }
    updateSelectOptions('excursions', data.excursions);
    updateSelectOptions('hotels', data.hotels);
    updateSelectOptions('flights', data.flights);
    $('#rooms').empty();

    // Обновляем авиабилеты, если выбрана авиакомпания
    const airlineId = $('select[name="airline"]').val();
    const date = $('#date').val();
    if (airlineId && cityId && date) {
      loadFlights(airlineId, cityId, date);
    } else {
      $('#flights').empty().prop('disabled', true);
    }
  });
});

// Загрузка комнат при выборе отеля
$('#hotels').change(function () {
  const selectedHotelId = $(this).val();
  if (selectedHotelId && selectedHotelId.length === 1) {
    $.getJSON('/get_rooms/' + selectedHotelId[0], function (data) {
      const select = $('#rooms');
      select.empty();
      data.rooms.forEach(function (room) {
        select.append(new Option(`${room.name} — ${room.type} — ${room.price} руб.`, room.id));
      });
    });
  } else {
    $('#rooms').empty();
  }
});

// Показ информации об экскурсиях
$('#excursions').change(function () {
  $('#excursion-info-container').empty();
  const selectedIds = $(this).val() || [];

  selectedIds.forEach(function (id) {
    $.getJSON('/get_excursion_info/' + id, function (data) {
      if (data.error) return;

      const block = 
        `<div class="excursion-info" style="border:1px solid #ccc; margin-bottom:10px; padding:10px;">
          <strong>${data.name}</strong><br>
          <b>Гид:</b> ${data.guide}<br>
          <b>Маршрут:</b> ${data.route}<br>
          <b>Дата:</b> ${data.date}<br>
          <b>Цена:</b> ${data.price} руб.
        </div>`;
      $('#excursion-info-container').append(block);
    });
  });
});

// Модальное окно создания экскурсии
$('#openExcursionModal').click(function () {
  $('#excursionModal, #modalBackdrop').show();
});

$('#cancelExcursion, #modalBackdrop').click(function () {
  $('#excursionModal, #modalBackdrop').hide();
  $('#excursionForm')[0].reset();
});

$('#excursionForm').submit(function (event) {
  event.preventDefault();

  let formData = $(this).serializeArray();
  formData.push({ name: 'city_id', value: $('#city').val() });

  $.ajax({
    url: excursionCreateUrl,
    method: 'POST',
    data: formData,
    success: function (response) {
      if (response.success) {
        let newOption = new Option(response.excursion.name, response.excursion.id, true, true);
        $('#excursions').append(newOption).trigger('change');

        alert('Экскурсия добавлена!');

        $('#excursionModal, #modalBackdrop').hide();
        $('#excursionForm')[0].reset();
      } else {
        alert('Ошибка при добавлении экскурсии: ' + response.error);
      }
    },
    error: function () {
      alert('Ошибка сервера при добавлении экскурсии');
    }
  });
});

// Функция загрузки авиабилетов с учётом авиакомпании, города и даты
function loadFlights(airlineId, cityId, date) {
  
  if (!date) {
    const flightsSelect = document.querySelector('select[name="flights"]');
    flightsSelect.innerHTML = '';
    flightsSelect.disabled = true;
    return;
  }

  fetch(`/get_flights_by_airline/${airlineId}?city_id=${cityId}&date=${date}`)
    .then(response => response.json())
    .then(data => {
      const flightsSelect = document.querySelector('select[name="flights"]');
      flightsSelect.innerHTML = '';
      data.forEach(flight => {
        const option = document.createElement('option');
        option.value = flight.id;
        option.textContent = flight.name;
        flightsSelect.appendChild(option);
      });
      flightsSelect.disabled = false;
    })
    .catch(() => {
      const flightsSelect = document.querySelector('select[name="flights"]');
      flightsSelect.innerHTML = '';
      flightsSelect.disabled = true;
    });
}

document.addEventListener('DOMContentLoaded', function () {
  const airlineSelect = document.querySelector('select[name="airline"]');
  const flightsSelect = document.querySelector('select[name="flights"]');
  const citySelect = document.querySelector('#city');
  const dateInput = document.querySelector('#date');

  if (!airlineSelect || !flightsSelect || !citySelect || !dateInput) return;

  flightsSelect.innerHTML = '';
  flightsSelect.disabled = true;

  function updateFlights() {
    const airlineId = airlineSelect.value;
    const cityId = citySelect.value;
    const date = dateInput.value;

    if (!airlineId || !cityId || !date) {
      flightsSelect.innerHTML = '';
      flightsSelect.disabled = true;
      return;
    }

    loadFlights(airlineId, cityId, date);
  }

  airlineSelect.addEventListener('change', updateFlights);
  citySelect.addEventListener('change', updateFlights);
  dateInput.addEventListener('change', updateFlights);
});

$(document).ready(function () {
  // Открытие/закрытие модального окна создания города
  $('#openCityModal').click(function () {
    $('#cityModal').show();
    $('#modalBackdrop').show();
  });

  $('#cancelCity').click(function () {
    $('#cityModal').hide();
    $('#modalBackdrop').hide();
  });

  $('#cityForm').submit(function (e) {
    e.preventDefault();
    const data = {
      name: $('input[name="name"]', this).val()
    };

    $.post(cityCreateUrl, data)
      .done(function (response) {
        const newOption = new Option(response.name, response.id, true, true);
        $('#city').append(newOption).trigger('change');
        $('#cityModal').hide();
        $('#modalBackdrop').hide();
      })
      .fail(function () {
        alert('Ошибка при создании города');
      });
  });

  // Открытие/закрытие модального окна создания отеля
  $('#openHotelModal').click(function () {
    $('#hotelModal, #modalBackdrop').show();
  });

  $('#cancelHotel, #modalBackdrop').click(function () {
    $('#hotelModal, #modalBackdrop').hide();
    $('#hotelForm')[0].reset();
  });

  // Автоматическая установка city_id в скрытое поле отеля
  const citySelect = document.getElementById('city');
  const hotelCityIdInput = document.querySelector('#hotelModal input[name="city_id"]');

  if (hotelCityIdInput && citySelect) {
    citySelect.addEventListener('change', function () {
      hotelCityIdInput.value = this.value;
    });
    hotelCityIdInput.value = citySelect.value;
  }

  // Отправка формы создания отеля через AJAX
  $('#hotelForm').submit(function (e) {
    e.preventDefault();

    const formData = $(this).serializeArray();
    formData.push({ name: 'city_id', value: $('#city').val() });

    $.ajax({
      url: hotelCreateUrl,
      method: 'POST',
      data: formData,
      success: function (response) {
        if (response.success) {
          const newOption = new Option(response.hotel.name, response.hotel.id, true, true);
          $('#hotels').append(newOption).trigger('change');

          alert('Отель добавлен!');
          $('#hotelModal, #modalBackdrop').hide();
          $('#hotelForm')[0].reset();
        } else {
          alert('Ошибка при добавлении отеля: ' + response.error);
        }
      },
      error: function () {
        alert('Ошибка сервера при добавлении отеля');
      }
    });
  });
});

// Показ информации о выбранном авиабилете
$('#flights').change(function () {
  $('#flight-info-container').empty();
  const selectedId = $(this).val();

  if (!selectedId) return;

  $.getJSON('/get_flight_info/' + selectedId, function (data) {
    if (data.error) return;

    const block = 
      `<div class="flight-info" style="border:1px solid #ccc; margin-top:10px; padding:10px;">
        <strong>${data.name}</strong><br>
        <b>Авиакомпания:</b> ${data.airline}<br>
        <b>Откуда:</b> ${data.from_city}<br>
        <b>Куда:</b> ${data.to_city}<br>
        <b>Дата:</b> ${data.date}<br>
        <b>Цена:</b> ${data.price} руб.
      </div>`;
    $('#flight-info-container').append(block);
  });
});

// Автоматическая установка hotel_id в скрытое поле при открытии модалки комнаты
$('#openRoomModal').click(function () {
  const selectedHotelId = $('#hotels').val();
  if (selectedHotelId && selectedHotelId.length === 1) {
    $('#roomModal input[name="hotel_id"]').val(selectedHotelId[0]);
  } else {
    alert('Пожалуйста, выберите один отель перед добавлением комнаты.');
    $('#roomModal, #modalBackdrop').hide();
  }
});

// --- Открытие/закрытие модального окна создания комнаты ---
$('#openRoomModal').click(function () {
  $('#roomModal, #modalBackdrop').show();
});

$('#cancelRoom, #modalBackdrop').click(function () {
  $('#roomModal, #modalBackdrop').hide();
  $('#roomForm')[0].reset();
});

// Автоматическая установка hotel_id в скрытое поле при открытии модалки комнаты
$('#openRoomModal').click(function () {
  const selectedHotelId = $('#hotels').val();
  if (selectedHotelId && selectedHotelId.length === 1) {
    $('#roomModal input[name="hotel_id"]').val(selectedHotelId[0]);
  } else {
    alert('Пожалуйста, выберите один отель перед добавлением комнаты.');
    $('#roomModal, #modalBackdrop').hide();
  }
});

// Обработка отправки формы создания комнаты через AJAX
$('#roomForm').submit(function (e) {
  e.preventDefault();

  const formData = $(this).serializeArray();

  $.ajax({
    url: roomCreateUrl, // url создания комнаты, должен быть передан из шаблона
    method: 'POST',
    data: formData,
    success: function (response) {
      if (response.success) {
        // Обновляем список комнат, добавляя новую комнату
        const select = $('#rooms');
        select.append(new Option(response.room.name + ' — ' + response.room.type + ' — ' + response.room.price + ' руб.', response.room.id));
        alert('Комната добавлена!');
        $('#roomModal, #modalBackdrop').hide();
        $('#roomForm')[0].reset();
      } else {
        alert('Ошибка при добавлении комнаты: ' + response.error);
      }
    },
    error: function () {
      alert('Ошибка сервера при добавлении комнаты');
    }
  });
});

$('#openAirlineModal').click(function () {
  $('#airlineModal, #modalBackdrop').show();
});

$('#cancelAirline, #modalBackdrop').click(function () {
  $('#airlineModal, #modalBackdrop').hide();
  $('#airlineForm')[0].reset();
});

$('#airlineForm').submit(function (e) {
  e.preventDefault();

  const formData = $(this).serialize();

  $.ajax({
    url: '/create_airline',  // должен совпадать с маршрутом Flask
    method: 'POST',
    data: formData,
    success: function (response) {
      if (response.success) {
        // Добавим новую авиакомпанию в select с выбором авиакомпании
        const newOption = new Option(response.airline.name, response.airline.id, true, true);
        $('select[name="airline"]').append(newOption).trigger('change');

        alert('Авиакомпания добавлена!');
        $('#airlineModal, #modalBackdrop').hide();
        $('#airlineForm')[0].reset();
      } else {
        alert('Ошибка: ' + response.error);
      }
    },
    error: function () {
      alert('Ошибка сервера при добавлении авиакомпании');
    }
  });
});

$(document).ready(function () {
  $('#openFlightModal').on('click', function () {
    const selectedCityName = $('#city option:selected').text();
    $('#to_city_input').val(selectedCityName);
    $('#flightModal, #modalBackdrop').show();
  });

  $('#cancelFlight, #modalBackdrop').on('click', function () {
    $('#flightModal, #modalBackdrop').hide();
    $('#flightForm')[0].reset();
  });

  $('#flightForm').off('submit').on('submit', function (e) {
    e.preventDefault();
    const data = new FormData(this);

    fetch("/create-flight", {
      method: "POST",
      body: data,
    })
    .then(response => {
      if (!response.ok) throw new Error("Ошибка при создании");
      return response.text();
    })
    .then(() => {
      alert("Авиабилет создан");
      this.reset();
      $('#flightModal, #modalBackdrop').hide();
      location.reload();
    })
    .catch(error => alert("Ошибка: " + error.message));
  });
});

const input = document.getElementById('tour_images');
const preview = document.getElementById('preview-container');

input.addEventListener('change', () => {
  preview.innerHTML = ''; // очищаем предыдущие превью

  const files = input.files;
  if (files.length === 0) {
    preview.innerHTML = '<p>Файлы не выбраны</p>';
    return;
  }

  for (const file of files) {
    if (!file.type.startsWith('image/')) continue;

    const img = document.createElement('img');
    img.style.width = '200px';
    img.style.height = 'auto';
    img.style.border = '1px solid #ddd';
    img.style.padding = '2px';
    img.style.borderRadius = '4px';
    img.style.objectFit = 'cover';

    const reader = new FileReader();
    reader.onload = e => {
      img.src = e.target.result;
      preview.appendChild(img);
    }
    reader.readAsDataURL(file);
  }
});